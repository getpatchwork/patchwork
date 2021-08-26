# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import codecs
import datetime
from email.header import decode_header
from email.header import make_header
from email.utils import mktime_tz
from email.utils import parsedate_tz
from email.errors import HeaderParseError
from fnmatch import fnmatch
import logging
import re

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.db import transaction

from patchwork.models import Cover
from patchwork.models import CoverComment
from patchwork.models import DelegationRule
from patchwork.models import get_default_initial_patch_state
from patchwork.models import Patch
from patchwork.models import PatchComment
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import SeriesReference
from patchwork.models import State


_hunk_re = re.compile(r'^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
_filename_re = re.compile(r'^(---|\+\+\+) (\S+)')
list_id_headers = ['List-ID', 'X-Mailing-List', 'X-list']

# How many minutes must pass since the first email of a series before we
# say that subsequent mails are definitely not part of that same series?
#
# Only used when there are not proper references to determine the series
# (such as when the mail is not threaded)
SERIES_DELAY_INTERVAL = 20

# @see https://git-scm.com/docs/git-diff#_generating_patches_with_p
EXTENDED_HEADER_LINES = (
    'old mode ', 'new mode ',
    'deleted file mode ', 'new file mode ',
    'copy from ', 'copy to ',
    'rename from ', 'rename to ',
    'similarity index ', 'dissimilarity index ',
    'new file mode ', 'index ')

logger = logging.getLogger(__name__)


class DuplicateMailError(Exception):

    def __init__(self, msgid):
        self.msgid = msgid


class DuplicateSeriesError(Exception):

    pass


def normalise_space(value):
    whitespace_re = re.compile(r'\s+')
    return whitespace_re.sub(' ', value).strip()


def sanitise_header(header_contents, header_name=None):
    """Clean and individual mail header.

    Given a header with header_contents, optionally labelled
    header_name, decode it with decode_header, sanitise it to make
    sure it decodes correctly and contains no invalid characters,
    then encode the result with make_header()
    """

    try:
        value = decode_header(header_contents)
    except HeaderParseError:
        # something has gone really wrong with header parsing.
        # (e.g. base64 decoding) We probably can't recover, so:
        return None

    # We have some issues here.
    #
    # Firstly, in the email parser (before we get here) headers with weird
    # chars are email.header.Header class, others as str
    #
    # Secondly, the behaviour of decode_header: weird headers are labelled
    # as unknown-8bit
    #
    # We solve this by catching any Unicode errors, and then manually
    # handling any interesting headers.

    try:
        header = make_header(value,
                             header_name=header_name,
                             continuation_ws='\t')
    except (UnicodeDecodeError, LookupError, ValueError):
        #  - a part cannot be encoded as ascii. (UnicodeDecodeError), or
        #  - we don't have a codec matching the hint (LookupError)
        #  - the codec has a null byte (ValueError)
        # Find out which part and fix it somehow.
        #
        # We get here under where decoding with the coding hint fails.

        new_value = []

        for (part, _) in value:
            # We have random bytes that aren't properly coded.
            # If we had a coding hint, it failed to help.

            # python3 - force coding to unknown-8bit
            new_value += [(part, 'unknown-8bit')]

        header = make_header(new_value,
                             header_name=header_name,
                             continuation_ws='\t')

    try:
        header.encode()
    except (HeaderParseError, IndexError):
        # despite our best efforts, the header is stuffed
        # HeaderParseError: some very weird multi-line headers
        # IndexError: bug, thrown by make_header(decode_header(' ')).encode()
        return None

    return header


def clean_header(header):
    """Decode (possibly non-ascii) headers."""

    sane_header = sanitise_header(header)

    if sane_header is None:
        return None

    header_str = str(sane_header)

    return normalise_space(header_str)


def find_project_by_id_and_subject(list_id, subject):
    """Find a `project` object based on `list_id` and subject match.
    Since empty `subject_match` field matches everything, project with
    given `list_id` and empty `subject_match` field serves as a default
    (in case it exists) if no other match is found.
    """
    projects = Project.objects.filter(listid=list_id)
    default = None
    for project in projects:
        if not project.subject_match:
            default = project
        elif re.search(project.subject_match, subject,
                       re.MULTILINE | re.IGNORECASE):
            return project

    return default


def find_project(mail, list_id=None):
    clean_subject = clean_header(mail.get('Subject', ''))

    if list_id:
        return find_project_by_id_and_subject(list_id, clean_subject)

    project = None
    listid_res = [re.compile(r'.*<([^>]+)>.*', re.S),
                  re.compile(r'^([\S]+)$', re.S)]

    for header in list_id_headers:
        if header in mail:
            h = clean_header(mail.get(header))
            if not h:
                continue

            for listid_re in listid_res:
                match = listid_re.match(h)
                if match:
                    break

            if not match:
                continue

            listid = match.group(1)

            project = find_project_by_id_and_subject(listid, clean_subject)
            if project:
                break

    if not project:
        logger.debug("Could not find a valid project for given list-id and "
                     "subject.")

    return project


def _find_series_by_references(project, mail):
    """Find a patch's series using message references.

    Traverse RFC822 headers, starting with most recent first, to find
    ancestors and the related series. Headers are traversed in reverse
    to handle series sent in reply to previous series, like so:

        [PATCH 0/3] A cover letter
          [PATCH 1/3] The first patch
          ...
          [PATCH v2 0/3] A cover letter
            [PATCH v2 1/3] The first patch
            ...

    This means we evaluate headers like so:

    - first, check for a Series that directly matches this message's
      Message-ID
    - then, check for a series that matches the In-Reply-To
    - then, check for a series that matches the References, from most
      recent (the patch's closest ancestor) to least recent

    Args:
        project (patchwork.Project): The project that the series
            belongs to
        mail (email.message.Message): The mail to extract series from

    Returns:
        The matching ``Series`` instance, if any
    """
    subject = mail.get('Subject')
    name, prefixes = clean_subject(subject, [project.linkname])
    version = parse_version(name, prefixes)

    refs = find_references(mail)
    h = clean_header(mail.get('Message-Id'))
    if h:
        refs = [h] + refs

    for ref in refs:
        try:
            series = SeriesReference.objects.get(
                msgid=ref[:255], project=project).series

            if series.version != version:
                # if the versions don't match, at least make sure these were
                # sent around the same time
                date = find_date(mail)
                delta = datetime.timedelta(minutes=SERIES_DELAY_INTERVAL)
                start_date = date - delta
                end_date = date + delta

                # ...and if they don't, this probably isn't our series
                if start_date > series.date > end_date:
                    continue

            # we want to return a queryset like '_find_series_by_markers'
            return Series.objects.filter(id=series.id)
        except SeriesReference.DoesNotExist:
            continue


def _find_series_by_markers(project, mail, author):
    """Find a patch's series using series markers and sender.

    Identify suitable series for a patch using a combination of the
    series markers found in the subject (version, number of patches)
    and the patch author. This is less reliable indicator than message
    headers and is subject to two main types of false positives that we
    must handle:

    - Series that are resubmitted, either by mistake or for some odd
      reason (perhaps the patches didn't show up immediately)
    - Series that have the same author, the same number of patches, and
      the same version, but which are in fact completely different
      series.

    To mitigate both cases, patches are also timeboxed such that any
    patches arriving SERIES_DELAY_INTERVAL minutes after the first
    patch in the series was created will not be grouped together. This
    still won't help us if someone spams the mailing list with
    duplicate series but that's a tricky situation for anyone to parse.
    """

    subject = mail.get('Subject')
    name, prefixes = clean_subject(subject, [project.linkname])
    _, total = parse_series_marker(prefixes)
    version = parse_version(name, prefixes)

    date = find_date(mail)
    delta = datetime.timedelta(minutes=SERIES_DELAY_INTERVAL)
    start_date = date - delta
    end_date = date + delta

    return Series.objects.filter(
        submitter=author, project=project, version=version, total=total,
        date__range=[start_date, end_date])


def find_series(project, mail, author):
    """Find a series, if any, for a given patch.

    Args:
        project (patchwork.Project): The project that the series
            belongs to
        mail (email.message.Message): The mail to extract series from

    Returns:
        The matching ``Series`` instance, if any
    """
    series = _find_series_by_references(project, mail)
    if series:
        return series

    return _find_series_by_markers(project, mail, author)


def split_from_header(from_header):
    name, email = (None, None)

    # tuple of (regex, fn)
    #  - where fn returns a (name, email) tuple from the match groups resulting
    #    from re.match().groups()
    # TODO(stephenfin): Perhaps we should check for "real" email addresses
    # instead of anything ('.*?')
    from_res = [
        # for "Firstname Lastname" <example@example.com> style addresses
        (re.compile(r'"?(.*?)"?\s*<([^>]+)>'), (lambda g: (g[0], g[1]))),

        # for example at example.com (Firstname Lastname) style addresses
        (re.compile(r'(.*?)\sat\s(.*?)\s*\(([^\)]+)\)'),
         (lambda g: (g[2], '@'.join(g[0:2])))),

        # for example@example.com (Firstname Lastname) style addresses
        (re.compile(r'"?(.*?)"?\s*\(([^\)]+)\)'), (lambda g: (g[1], g[0]))),

        # everything else
        (re.compile(r'(.*)'), (lambda g: (None, g[0]))),
    ]

    for regex, fn in from_res:
        match = regex.match(from_header)
        if match:
            (name, email) = fn(match.groups())
            break

    return (name, email)


# Unmangle From addresses that have been mangled for DMARC purposes.
#
# To avoid triggering spam filters due to failed signature validation, many
# mailing lists mangle the From header to change the From address to be the
# address of the list, typically where the sender's domain has a strict
# DMARC policy enabled.
#
# Unfortunately, there's no standardised way of preserving the original
# From address.
#
# Google Groups adds an X-Original-From header. If present, we use that.
#
# Mailman preserves the original address by adding a Reply-To, except in the
# case where the list is set to either reply to list, or reply to a specific
# address, in which case the original From is added to Cc instead. These corner
# cases are dumb, but we try and handle things as sensibly as possible by
# looking for a name in Reply-To/Cc that matches From. It's inexact but should
# be good enough for our purposes.
def get_original_sender(mail, name, email):
    if name and ' via ' in name:
        # Mailman uses the format "<name> via <list>"
        # Google Groups uses "'<name>' via <list>"
        stripped_name = name[:name.rfind(' via ')].strip().strip("'")
    elif name.endswith(' via'):
        # Sometimes this seems to happen (perhaps if Mailman isn't set up with
        # any list name)
        stripped_name = name[:name.rfind(' via')].strip().strip("'")
    else:
        # We've hit a format that we don't expect
        stripped_name = None

    original_from = clean_header(mail.get('X-Original-From', ''))
    if original_from:
        new_email = split_from_header(original_from)[1].strip()[:255]
        return (stripped_name, new_email)

    addrs = []
    reply_to_headers = mail.get_all('Reply-To') or []
    cc_headers = mail.get_all('Cc') or []
    for header in reply_to_headers + cc_headers:
        header = clean_header(header)
        addrs = header.split(",")
        for addr in addrs:
            new_name, new_email = split_from_header(addr)
            if new_name:
                new_name = new_name.strip()[:255]
            if new_email:
                new_email = new_email.strip()[:255]
            if new_name == stripped_name:
                return (stripped_name, new_email)

    # If we can't figure out the original sender, just keep it as is
    return (name, email)


def get_or_create_author(mail, project=None):
    from_header = clean_header(mail.get('From'))

    if not from_header:
        raise ValueError("Invalid 'From' header")

    name, email = split_from_header(from_header)

    if not email:
        raise ValueError("Invalid 'From' header")

    email = email.strip()[:255]
    if name is not None:
        name = name.strip()[:255]

    if project and email.lower() == project.listemail.lower():
        name, email = get_original_sender(mail, name, email)

    # this correctly handles the case where we lose the race to create
    # the person and another process beats us to it. (If the record
    # does not exist, g_o_c invokes _create_object_from_params which
    # catches the IntegrityError and repeats the SELECT.)
    person = Person.objects.get_or_create(email__iexact=email,
                                          defaults={'name': name,
                                                    'email': email})[0]

    if name and name != person.name:  # use the latest provided name
        person.name = name
        person.save()

    return person


def find_date(mail):
    h = clean_header(mail.get('Date', ''))
    if not h:
        return datetime.datetime.utcnow()

    t = parsedate_tz(h)
    if not t:
        return datetime.datetime.utcnow()

    try:
        d = datetime.datetime.utcfromtimestamp(mktime_tz(t))
    except (OverflowError, ValueError, OSError):
        # If you have a date like:
        # - Date: Wed, 4 Jun 207777777777777777777714 17:50:46 0
        #   -> OverflowError
        # - Date:, 11 Sep 2016 23:22:904070804030804 +0100
        #   -> ValueError
        # - Date:, 11 Sep 2016 407080403080105:04 +0100
        #   -> OSError (Python 3)
        d = datetime.datetime.utcnow()

    return d


def find_headers(mail):
    headers = [(key, sanitise_header(value, header_name=key))
               for key, value in mail.items()]

    strings = [('%s: %s' % (key, header.encode()))
               for (key, header) in headers if header is not None]

    return '\n'.join(strings)


def find_references(mail):
    """Construct a list of possible reply message ids.

    Extract 'in-reply-to' and 'references' headers from a given mail
    and return the combined set of each. Because headers can be
    duplicated, 'get_all' is used rather than 'get'.
    """
    refs = []

    if 'In-Reply-To' in mail:
        for in_reply_to in mail.get_all('In-Reply-To'):
            r = clean_header(in_reply_to)
            if r:
                refs.append(r)

    if 'References' in mail:
        for references_header in mail.get_all('References'):
            h = clean_header(references_header)
            if not h:
                continue
            references = h.split()
            references.reverse()
            for ref in references:
                ref = ref.strip()
                if ref not in refs:
                    refs.append(ref)

    return refs


def _find_matching_prefix(subject_prefixes, regex):
    for prefix in subject_prefixes:
        m = regex.match(prefix)
        if m:
            return m


def parse_series_marker(subject_prefixes):
    """Extract series markers from subject.

    Extract the markers of multi-patches series, i.e. 'x/n', from the
    provided subject series.

    Args:
        subject_prefixes: List of subject prefixes to extract markers
          from

    Returns:
        (x, n) if markers found, else (None, None)
    """

    # Allow for there to be stuff before the number. This allows for
    # e.g. "PATCH1/8" which we have seen in the wild. To allow
    # e.g. PATCH100/123 to work, make the pre-number match
    # non-greedy. To allow really pathological cases like v2PATCH12/15
    # to work, allow it to match everthing (don't exclude numbers).
    regex = re.compile(r'.*?([0-9]+)(?:/| of )([0-9]+)$')
    m = _find_matching_prefix(subject_prefixes, regex)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    return (None, None)


def parse_version(subject, subject_prefixes):
    """Extract patch version.

    Args:
        subject: Main body of subject line
        subject_prefixes: List of subject prefixes to extract version
          from

    Returns:
        version if found, else 1
    """
    regex = re.compile(r'^[vV](\d+)$')
    m = _find_matching_prefix(subject_prefixes, regex)
    if m:
        return int(m.group(1))

    m = re.search(r'\([vV](\d+)\)', subject)
    if m:
        return int(m.group(1))

    return 1


def _find_content(mail):
    """Extract the payload(s) from a mail.

    Handles various payload types.

    :returns: A list of tuples, corresponding the payload and subtype
        of payload.
    """
    results = []

    for part in mail.walk():
        if part.get_content_maintype() != 'text':
            continue

        payload = part.get_payload(decode=True)
        subtype = part.get_content_subtype()

        if not isinstance(payload, str):
            charset = part.get_content_charset()

            # Check that we have a charset that we understand. Otherwise,
            # ignore it and fallback to our standard set.
            if charset is not None:
                try:
                    codecs.lookup(charset)
                except (LookupError, ValueError, TypeError):
                    charset = None

            # If there is no charset or if it is unknown, then try some common
            # charsets before we fail.
            if charset is None:
                try_charsets = ['utf-8', 'windows-1252', 'iso-8859-1']
            else:
                try_charsets = [charset]

            for cset in try_charsets:
                try:
                    new_payload = payload.decode(cset)
                    break
                except UnicodeDecodeError:
                    new_payload = None
            payload = new_payload

            # Could not find a valid decoded payload.  Fail.
            if payload is None:
                continue

        results.append((payload, subtype))

    return results


def find_patch_content(mail):
    """Extract a comment and potential diff from a mail."""
    patchbuf = None
    commentbuf = ''

    for payload, subtype in _find_content(mail):
        if subtype in ['x-patch', 'x-diff']:
            patchbuf = payload
        elif subtype == 'plain':
            c = payload

            if not patchbuf:
                patchbuf, c = parse_patch(payload)

            if c is not None:
                commentbuf += c.strip() + '\n'

    commentbuf = clean_content(commentbuf)

    return patchbuf, commentbuf


def find_comment_content(mail):
    """Extract content from a mail."""
    commentbuf = ''

    for payload, subtype in _find_content(mail):
        if not payload:
            continue

        if subtype != 'plain':
            continue

        commentbuf += payload.strip() + '\n'

    commentbuf = clean_content(commentbuf)

    # keep the method signature the same as find_patch_content
    return None, commentbuf


def find_patch_for_comment(project, refs):
    for ref in refs:
        ref = ref[:255]
        # first, check for a direct reply
        try:
            patch = Patch.objects.get(project=project, msgid=ref)
            return patch
        except Patch.DoesNotExist:
            pass

        # see if we have comments that refer to a patch
        try:
            comment = PatchComment.objects.get(
                patch__project=project,
                msgid=ref,
            )
            return comment.patch
        except PatchComment.MultipleObjectsReturned:
            # NOTE(stephenfin): This is a artifact of prior lack of support
            # for cover letters in Patchwork. Previously all replies to
            # patches were saved as comments. However, it's possible that
            # someone could have created a new series as a reply to one of the
            # comments on the original patch series. For example,
            # '2015-November/002096.html' from the Patchwork archives. In this
            # case, reparsing the archives will result in creation of a cover
            # letter with the same message ID as the existing comment. Follow
            # up comments will then apply to both this cover letter and the
            # linked patch from the comment previously created. We choose to
            # apply the comment to the cover letter. Note that this only
            # happens when running 'parsearchive' or similar, so it should not
            # affect every day use in any way.
            comments = PatchComment.objects.filter(
                patch__project=project,
                msgid=ref,
            )
            # The latter item will be the cover letter
            return comments.reverse()[0].patch
        except PatchComment.DoesNotExist:
            pass

    return None


def find_cover_for_comment(project, refs):
    for ref in refs:
        ref = ref[:255]
        # first, check for a direct reply
        try:
            cover = Cover.objects.get(project=project, msgid=ref)
            return cover
        except Cover.DoesNotExist:
            pass

        # see if we have comments that refer to a patch
        try:
            comment = CoverComment.objects.get(
                cover__project=project,
                msgid=ref,
            )
            return comment.cover
        except CoverComment.DoesNotExist:
            pass

    return None


def split_prefixes(prefix):
    """Turn a prefix string into a list of prefix tokens."""
    tokens = []
    # detect mercurial series marker (M of N)
    series_re = re.compile(r'^PATCH (\d+ of \d+)(.*)$')
    match = series_re.match(prefix)
    if match is not None:
        series, prefix = match.groups()
        tokens.extend(['PATCH', series])
    split_re = re.compile(r'[,\s]+')
    matches = split_re.split(prefix)
    tokens.extend([s for s in matches if s != ''])
    return tokens


def clean_subject(subject, drop_prefixes=None):
    """Clean a Subject: header from an incoming patch.

    Removes Re: and Fwd: strings, as well as [PATCH]-style prefixes. By
    default, only [PATCH] is removed, and we keep any other bracketed
    data in the subject. If drop_prefixes is provided, remove those
    too, comparing case-insensitively.

    Args:
        subject: Subject to be cleaned
        drop_prefixes: Additional, case-insensitive prefixes to remove
          from the subject
    """
    re_re = re.compile(r'^(re|fwd?)[:\s]\s*', re.I)
    prefix_re = re.compile(r'^\[([^\]]*)\]\s*(.*)$')
    subject = clean_header(subject)

    if subject is None:
        raise ValueError("Invalid 'Subject' header")

    if drop_prefixes is None:
        drop_prefixes = []
    else:
        drop_prefixes = [s.lower() for s in drop_prefixes]

    drop_prefixes.append('patch')

    # remove Re:, Fwd:, etc
    subject = re_re.sub(' ', subject)

    subject = normalise_space(subject)

    prefixes = []

    match = prefix_re.match(subject)

    while match:
        prefix_str = match.group(1)
        prefixes += [p for p in split_prefixes(prefix_str)
                     if p.lower() not in drop_prefixes]

        subject = match.group(2)
        match = prefix_re.match(subject)

    subject = normalise_space(subject)
    if prefixes:
        subject = '[%s] %s' % (','.join(prefixes), subject)

    return (subject, prefixes)


def subject_check(subject):
    """Determine if a mail is a reply."""
    comment_re = re.compile(r'^(re)[:\s]\s*', re.I)

    h = clean_header(subject)
    if not h:
        return False

    return comment_re.match(h)


def clean_content(content):
    """Remove cruft from the email message.

    Catch signature (-- ) and list footer (_____) cruft.
    """
    sig_re = re.compile(r'^(-- |_+)\n.*', re.S | re.M)
    content = sig_re.sub('', content)

    return content.strip()


def parse_patch(content):
    """Split a mail's contents into a diff and comment.

    This is a state machine that takes a patch, generally in UNIX mbox
    format, and splits it into the component comments and diff.

    Args:
        patch: The patch to be split

    Returns:
        A tuple containing the diff and comment. Either one or both of
        these can be empty.

    Raises:
        Exception: The state machine transitioned to an invalid state.
    """
    patchbuf = ''
    commentbuf = ''
    buf = ''

    # state specified the line we just saw, and what to expect next
    state = 0
    # 0: text
    # 1: suspected patch header (diff, Index:)
    # 2: patch header line 1 (---)
    # 3: patch header line 2 (+++)
    # 4: patch hunk header line (@@ line)
    # 5: patch hunk content
    # 6: patch meta header (rename from/rename to/new file/index)
    #
    # valid transitions:
    #  0 -> 1 (diff, Index:)
    #  0 -> 2 (---)
    #  1 -> 2 (---)
    #  2 -> 3 (+++)
    #  3 -> 4 (@@ line)
    #  4 -> 5 (patch content)
    #  5 -> 1 (run out of lines from @@-specifed count)
    #  1 -> 6 (extended header lines)
    #  6 -> 2 (---)
    #  6 -> 1 (other text)
    #
    # Suspected patch header is stored into buf, and appended to
    # patchbuf if we find a following hunk. Otherwise, append to
    # comment after parsing.

    # line counts while parsing a patch hunk
    lc = (0, 0)
    hunk = 0

    for line in content.split('\n'):
        line += '\n'

        if state == 0:
            if line.startswith('diff ') \
                    or line.startswith('Index: '):
                state = 1
                buf += line
            elif line.startswith('--- '):
                state = 2
                buf += line
            else:
                commentbuf += line
        elif state == 1:
            buf += line
            if line.startswith('--- '):
                state = 2
            if line.startswith(EXTENDED_HEADER_LINES):
                state = 6
        elif state == 2:
            if line.startswith('+++ '):
                state = 3
                buf += line
            elif hunk:
                state = 1
                buf += line
            else:
                state = 0
                commentbuf += buf + line
                buf = ''
        elif state == 3:
            match = _hunk_re.match(line)
            if match:
                def fn(x):
                    if not x:
                        return 1
                    return int(x)

                lc = [fn(x) for x in match.groups()]

                state = 4
                patchbuf += buf + line
                buf = ''
            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2
            elif hunk and line.startswith(r'\ No newline at end of file'):
                # If we had a hunk and now we see this, it's part of the patch,
                # and we're still expecting another @@ line.
                patchbuf += line
            elif hunk:
                state = 1
                buf += line
            else:
                state = 0
                commentbuf += buf + line
                buf = ''
        elif state in [4, 5]:
            if line.startswith('-'):
                lc[0] -= 1
            elif line.startswith('+'):
                lc[1] -= 1
            elif line.startswith(r'\ No newline at end of file'):
                # Special case: Not included as part of the hunk's line count
                pass
            else:
                lc[0] -= 1
                lc[1] -= 1

            patchbuf += line

            if lc[0] <= 0 and lc[1] <= 0:
                state = 3
                hunk += 1
            else:
                state = 5
        elif state == 6:
            if line.startswith(EXTENDED_HEADER_LINES):
                patchbuf += buf + line
                buf = ''
            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2
            else:
                buf += line
                state = 1
        else:
            raise Exception("Unknown state %d! (line '%s')" % (state, line))

    commentbuf += buf

    if patchbuf == '':
        patchbuf = None

    if commentbuf == '':
        commentbuf = None

    return patchbuf, commentbuf


def parse_pull_request(content):
    git_re = re.compile(
        r'^The following changes since commit.*'
        r'^are available in the git repository at:\s*\n'
        r'^\s*([\w+-]+(?:://|@)[\w/.@:~-]+[\s\\]*[\w/._-]*)\s*$',
        re.DOTALL | re.MULTILINE | re.IGNORECASE)
    match = git_re.search(content)
    if match:
        return re.sub(r'\s+', ' ', match.group(1)).strip()
    return None


def find_state(mail):
    """Return the state with the given name or the default."""
    state_name = clean_header(mail.get('X-Patchwork-State', ''))
    if state_name:
        try:
            return State.objects.get(name__iexact=state_name)
        except State.DoesNotExist:
            pass
    return get_default_initial_patch_state()


def find_delegate_by_filename(project, filenames):
    if not filenames:
        return None

    rules = list(DelegationRule.objects.filter(project=project))

    patch_delegate = None

    for filename in filenames:
        file_delegate = None
        for rule in rules:
            if fnmatch(filename, rule.path):
                file_delegate = rule.user
                break

        if file_delegate is None:
            return None

        if patch_delegate is not None and file_delegate != patch_delegate:
            return None

        patch_delegate = file_delegate

    return patch_delegate


def find_delegate_by_header(mail):
    """Return the delegate with the given email or None."""
    delegate_email = clean_header(mail.get('X-Patchwork-Delegate', ''))
    if delegate_email:
        try:
            return User.objects.get(email__iexact=delegate_email)
        except User.DoesNotExist:
            pass

    return None


def find_comment_addressed_by_header(mail):
    """Determine whether a comment is actionable or not."""
    # we dispose of the value - it's irrelevant
    return False if 'X-Patchwork-Action-Required' in mail else None


def parse_mail(mail, list_id=None):
    """Parse a mail and add to the database.

    Args:
        mail (`mbox.Mail`): Mail to parse and add.
        list_id (str): Mailing list ID

    Returns:
        patch/cover letter/comment
        Or None if nothing is found in the mail
                   or X-P-H: ignore
                   or project not found

    Raises:
        ValueError if there is an error in parsing or a duplicate mail
        Other truly unexpected issues may bubble up from the DB.
    """
    # some basic sanity checks
    if 'From' not in mail:
        raise ValueError("Missing 'From' header")

    if 'Subject' not in mail:
        raise ValueError("Missing 'Subject' header")

    if 'Message-Id' not in mail:
        raise ValueError("Missing 'Message-Id' header")

    hint = clean_header(mail.get('X-Patchwork-Hint', ''))
    if hint and hint.lower() == 'ignore':
        logger.info("Ignoring email due to 'ignore' hint")
        return

    project = find_project(mail, list_id)

    if project is None:
        logger.error('Failed to find a project for email')
        return

    # parse metadata

    msgid = clean_header(mail.get('Message-Id'))
    if not msgid:
        raise ValueError("Broken 'Message-Id' header")
    msgid = msgid[:255]

    subject = mail.get('Subject')
    name, prefixes = clean_subject(subject, [project.linkname])
    is_comment = subject_check(subject)
    x, n = parse_series_marker(prefixes)
    version = parse_version(name, prefixes)
    refs = find_references(mail)
    date = find_date(mail)
    headers = find_headers(mail)

    # parse content

    if not is_comment:
        diff, message = find_patch_content(mail)
    else:
        diff, message = find_comment_content(mail)

    if not (diff or message):
        return  # nothing to work with

    pull_url = parse_pull_request(message)

    # build objects

    if not is_comment and (diff or pull_url):  # patches or pull requests
        # we delay the saving until we know we have a patch.
        author = get_or_create_author(mail, project)

        delegate = find_delegate_by_header(mail)
        if not delegate and diff:
            filenames = find_filenames(diff)
            delegate = find_delegate_by_filename(project, filenames)

        with transaction.atomic():
            if Patch.objects.filter(project=project, msgid=msgid):
                raise DuplicateMailError(msgid=msgid)

            patch = Patch.objects.create(
                msgid=msgid,
                project=project,
                name=name[:255],
                date=date,
                headers=headers,
                submitter=author,
                content=message,
                diff=diff,
                pull_url=pull_url,
                delegate=delegate,
                state=find_state(mail))
            logger.debug('Patch saved')

        for attempt in range(1, 11):  # arbitrary retry count
            try:
                with transaction.atomic():
                    # if we don't have a series marker, we will never have an
                    # existing series to match against.
                    series = None
                    if n:
                        series = find_series(project, mail, author)
                        if len(series) > 1:
                            # if this isn't our final attempt, go again
                            if attempt != 10:
                                raise DuplicateSeriesError()

                            # if it is and we still haven't been able to save a
                            # series, it's time to give up and just save yet
                            # another duplicate - find the best possible match
                            for series in series.order_by('-date'):
                                if Patch.objects.filter(
                                        series=series, number=x).count():
                                    continue
                                break
                            else:
                                series = None
                        elif len(series) == 1:
                            series = series.first()
                    else:
                        x = n = 1

                    # We will create a new series if:
                    # - there is no existing series to assign this patch to, or
                    # - there is an existing series, but it already has a patch
                    #   with this number in it
                    if not series or Patch.objects.filter(
                            series=series, number=x).count():
                        series = Series.objects.create(
                            project=project,
                            date=date,
                            submitter=author,
                            version=version,
                            total=n)

                        # NOTE(stephenfin) We must save references for series.
                        # We do this to handle the case where a later patch is
                        # received first. Without storing references, it would
                        # not be possible to identify the relationship between
                        # patches as the earlier patch does not reference the
                        # later one.
                        for ref in refs + [msgid]:
                            ref = ref[:255]
                            # we don't want duplicates
                            try:
                                # we could have a ref to a previous series.
                                # (For example, a series sent in reply to
                                # another series.) That should not create a
                                # series ref for this series, so check for the
                                # msg-id only, not the msg-id/series pair.
                                SeriesReference.objects.get(
                                    msgid=ref, project=project)
                            except SeriesReference.DoesNotExist:
                                SeriesReference.objects.create(
                                    msgid=ref, project=project, series=series)

                        # attempt to pull the series in again, raising an
                        # exception if we lost the race when creating a series
                        # and force us to go through this again
                        if attempt != 10 and find_series(
                                project, mail, author).count() > 1:
                            raise DuplicateSeriesError()

                    break
            except (IntegrityError, DuplicateSeriesError):
                # we lost the race so go again
                logger.warning('Conflict while saving series. This is '
                               'probably because multiple patches belonging '
                               'to the same series have been received at '
                               'once. Trying again (attempt %02d/10)',
                               attempt)
        else:
            # we failed to save the series so return the series-less patch
            logger.warning('Failed to save series. Your patch with message ID '
                           '%s has been saved but this should not happen. '
                           'Please report this as a bug and include logs',
                           msgid)
            return patch

        # add to a series if we have found one, and we have a numbered
        # patch. Don't add unnumbered patches (for example diffs sent
        # in reply, or just messages with random refs/in-reply-tos)
        if series and x:
            # TODO(stephenfin): Remove 'series' from the conditional as we will
            # always have a series
            series.add_patch(patch, x)

        return patch
    elif x == 0:  # (potential) cover letters
        # if refs are empty, it's implicitly a cover letter. If not,
        # however, we need to see if a match already exists and, if
        # not, assume that it is indeed a new cover letter
        is_cover_letter = False
        if not is_comment:
            if not refs == []:
                try:
                    Cover.objects.all().get(name=name)
                except Cover.DoesNotExist:
                    # if no match, this is a new cover letter
                    is_cover_letter = True
                except Cover.MultipleObjectsReturned:
                    # if multiple cover letters are found, just ignore
                    pass
            else:
                is_cover_letter = True

        if is_cover_letter:
            author = get_or_create_author(mail, project)

            # we don't use 'find_series' here as a cover letter will
            # always be the first item in a thread, thus the references
            # could only point to a different series or unrelated
            # message
            try:
                series = SeriesReference.objects.get(
                    msgid=msgid, project=project).series
            except SeriesReference.DoesNotExist:
                series = None

            if not series:
                series = Series.objects.create(
                    project=project,
                    date=date,
                    submitter=author,
                    version=version,
                    total=n)

                # we don't save the in-reply-to or references fields
                # for a cover letter, as they can't refer to the same
                # series
                SeriesReference.objects.create(
                    msgid=msgid, project=project, series=series)

            with transaction.atomic():
                if Cover.objects.filter(project=project, msgid=msgid):
                    raise DuplicateMailError(msgid=msgid)

                cover_letter = Cover.objects.create(
                    msgid=msgid,
                    project=project,
                    name=name[:255],
                    date=date,
                    headers=headers,
                    submitter=author,
                    content=message)

            logger.debug('Cover letter saved')

            series.add_cover_letter(cover_letter)

            return cover_letter

    # comments

    # we only save comments if we have the parent email
    patch = find_patch_for_comment(project, refs)
    if patch:
        author = get_or_create_author(mail, project)
        addressed = find_comment_addressed_by_header(mail)

        with transaction.atomic():
            if PatchComment.objects.filter(patch=patch, msgid=msgid):
                raise DuplicateMailError(msgid=msgid)
            comment = PatchComment.objects.create(
                patch=patch,
                msgid=msgid,
                date=date,
                headers=headers,
                submitter=author,
                content=message,
                addressed=addressed)

        logger.debug('Comment saved')

        return comment

    cover = find_cover_for_comment(project, refs)
    if not cover:
        return

    author = get_or_create_author(mail, project)

    with transaction.atomic():
        if CoverComment.objects.filter(cover=cover, msgid=msgid):
            raise DuplicateMailError(msgid=msgid)
        comment = CoverComment.objects.create(
            cover=cover,
            msgid=msgid,
            date=date,
            headers=headers,
            submitter=author,
            content=message)

    logger.debug('Comment saved')

    return comment


def find_filenames(diff):
    """Find files changes in a given diff."""
    # normalise spaces
    diff = diff.replace('\r', '')
    diff = diff.strip() + '\n'

    filenames = {}

    for line in diff.split('\n'):
        if len(line) <= 0:
            continue

        filename_match = _filename_re.match(line)
        if not filename_match:
            continue

        filename = filename_match.group(2)
        if filename.startswith('/dev/null'):
            continue

        filename = '/'.join(filename.split('/')[1:])
        filenames[filename] = True

    filenames = sorted(filenames.keys())

    return filenames
