#!/usr/bin/env python
#
# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# This file is part of the Patchwork package.
#
# Patchwork is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Patchwork is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Patchwork; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import codecs
import datetime
from email.header import Header, decode_header
from email.utils import parsedate_tz, mktime_tz
from fnmatch import fnmatch
from functools import reduce
import logging
import operator
import re

from django.contrib.auth.models import User
from django.utils import six
from django.utils.six.moves import map

from patchwork.models import (Patch, Project, Person, Comment, State,
                              DelegationRule, Submission, CoverLetter,
                              get_default_initial_patch_state)


_hunk_re = re.compile(r'^\@\@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? \@\@')
_filename_re = re.compile(r'^(---|\+\+\+) (\S+)')
list_id_headers = ['List-ID', 'X-Mailing-List', 'X-list']

LOGGER = logging.getLogger(__name__)


def normalise_space(str):
    whitespace_re = re.compile(r'\s+')
    return whitespace_re.sub(' ', str).strip()


def clean_header(header):
    """Decode (possibly non-ascii) headers."""
    def decode(fragment):
        (frag_str, frag_encoding) = fragment
        if frag_encoding:
            return frag_str.decode(frag_encoding)
        elif isinstance(frag_str, six.binary_type):  # python 2
            return frag_str.decode()
        return frag_str

    fragments = list(map(decode, decode_header(header)))

    return normalise_space(u' '.join(fragments))


def find_project_by_id(list_id):
    """Find a `project` object with given `list_id`."""
    project = None
    try:
        project = Project.objects.get(listid=list_id)
    except Project.DoesNotExist:
        pass
    return project


def find_project_by_header(mail):
    project = None
    listid_res = [re.compile(r'.*<([^>]+)>.*', re.S),
                  re.compile(r'^([\S]+)$', re.S)]

    for header in list_id_headers:
        if header in mail:

            for listid_re in listid_res:
                match = listid_re.match(mail.get(header))
                if match:
                    break

            if not match:
                continue

            listid = match.group(1)

            project = find_project_by_id(listid)
            if project:
                break

    return project


def find_author(mail):
    from_header = clean_header(mail.get('From'))
    name, email = (None, None)

    # tuple of (regex, fn)
    #  - where fn returns a (name, email) tuple from the match groups resulting
    #    from re.match().groups()
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

    if email is None:
        raise ValueError("Invalid 'From' header")

    email = email.strip()
    if name is not None:
        name = name.strip()

    try:
        person = Person.objects.get(email__iexact=email)
        if name:  # use the latest provided name
            person.name = name
    except Person.DoesNotExist:
        person = Person(name=name, email=email)

    return person


def find_date(mail):
    t = parsedate_tz(mail.get('Date', ''))
    if not t:
        return datetime.datetime.utcnow()
    return datetime.datetime.utcfromtimestamp(mktime_tz(t))


def find_headers(mail):
    return reduce(operator.__concat__,
                  ['%s: %s\n' % (k, Header(v, header_name=k,
                                           continuation_ws='\t').encode())
                   for (k, v) in list(mail.items())])


def find_references(mail):
    """Construct a list of possible reply message ids."""
    refs = []

    if 'In-Reply-To' in mail:
        refs.append(mail.get('In-Reply-To'))

    if 'References' in mail:
        rs = mail.get('References').split()
        rs.reverse()
        for r in rs:
            if r not in refs:
                refs.append(r)

    return refs


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

    regex = re.compile('^([0-9]+)/([0-9]+)$')
    for prefix in subject_prefixes:
        m = regex.match(prefix)
        if not m:
            continue
        return (int(m.group(1)), int(m.group(2)))
    return (None, None)


def find_content(project, mail):
    """Extract a comment and potential diff from a mail."""
    patchbuf = None
    commentbuf = ''

    for part in mail.walk():
        if part.get_content_maintype() != 'text':
            continue

        payload = part.get_payload(decode=True)
        subtype = part.get_content_subtype()

        if not isinstance(payload, six.text_type):
            charset = part.get_content_charset()

            # Check that we have a charset that we understand. Otherwise,
            # ignore it and fallback to our standard set.
            if charset is not None:
                try:
                    codecs.lookup(charset)
                except LookupError:
                    charset = None

            # If there is no charset or if it is unknown, then try some common
            # charsets before we fail.
            if charset is None:
                try_charsets = ['utf-8', 'windows-1252', 'iso-8859-1']
            else:
                try_charsets = [charset]

            for cset in try_charsets:
                try:
                    payload = six.text_type(payload, cset)
                    break
                except UnicodeDecodeError:
                    payload = None

            # Could not find a valid decoded payload.  Fail.
            if payload is None:
                return None, None

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


def find_submission_for_comment(project, refs):
    for ref in refs:
        # first, check for a direct reply
        try:
            submission = Submission.objects.get(project=project, msgid=ref)
            return submission
        except Submission.DoesNotExist:
            pass

        # see if we have comments that refer to a patch
        try:
            comment = Comment.objects.get(submission__project=project,
                                          msgid=ref)
            return comment.submission
        except Comment.MultipleObjectsReturned:
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
            comments = Comment.objects.filter(submission__project=project,
                                              msgid=ref)
            # The latter item will be the cover letter
            return comments.reverse()[0].submission
        except Comment.DoesNotExist:
            pass

    return None


def split_prefixes(prefix):
    """Turn a prefix string into a list of prefix tokens."""
    split_re = re.compile(r'[,\s]+')
    matches = split_re.split(prefix)

    return [s for s in matches if s != '']


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

    subject = subject.strip()
    if prefixes:
        subject = '[%s] %s' % (','.join(prefixes), subject)

    return (subject, prefixes)


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
    # 1: suspected patch header (diff, ====, Index:)
    # 2: patch header line 1 (---)
    # 3: patch header line 2 (+++)
    # 4: patch hunk header line (@@ line)
    # 5: patch hunk content
    # 6: patch meta header (rename from/rename to)
    #
    # valid transitions:
    #  0 -> 1 (diff, ===, Index:)
    #  0 -> 2 (---)
    #  1 -> 2 (---)
    #  2 -> 3 (+++)
    #  3 -> 4 (@@ line)
    #  4 -> 5 (patch content)
    #  5 -> 1 (run out of lines from @@-specifed count)
    #  1 -> 6 (rename from / rename to)
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
            if line.startswith('diff ') or line.startswith('===') \
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

            if line.startswith(('rename from ', 'rename to ')):
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

                lc = list(map(fn, match.groups()))

                state = 4
                patchbuf += buf + line
                buf = ''
            elif line.startswith('--- '):
                patchbuf += buf + line
                buf = ''
                state = 2
            elif hunk and line.startswith('\ No newline at end of file'):
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
        elif state == 4 or state == 5:
            if line.startswith('-'):
                lc[0] -= 1
            elif line.startswith('+'):
                lc[1] -= 1
            elif line.startswith('\ No newline at end of file'):
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
            if line.startswith(('rename to ', 'rename from ')):
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
    git_re = re.compile(r'^The following changes since commit.*' +
                        r'^are available in the git repository at:\n'
                        r'^\s*([\S]+://[^\n]+)$',
                        re.DOTALL | re.MULTILINE)
    match = git_re.search(content)
    if match:
        return match.group(1)
    return None


def find_state(mail):
    """Return the state with the given name or the default."""
    state_name = mail.get('X-Patchwork-State', '').strip()
    if state_name:
        try:
            return State.objects.get(name__iexact=state_name)
        except State.DoesNotExist:
            pass
    return get_default_initial_patch_state()


def auto_delegate(project, filenames):
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


def find_delegate(mail):
    """Return the delegate with the given email or None."""
    delegate_email = mail.get('X-Patchwork-Delegate', '').strip()
    if delegate_email:
        try:
            return User.objects.get(email__iexact=delegate_email)
        except User.DoesNotExist:
            pass
    return None


def parse_mail(mail, list_id=None):
    """Parse a mail and add to the database.

    Args:
        mail (`mbox.Mail`): Mail to parse and add.
        list_id (str): Mailing list ID

    Returns:
        None
    """
    # some basic sanity checks
    if 'From' not in mail:
        raise ValueError("Missing 'From' header")

    if 'Subject' not in mail:
        raise ValueError("Missing 'Subject' header")

    if 'Message-Id' not in mail:
        raise ValueError("Missing 'Message-Id' header")

    hint = mail.get('X-Patchwork-Hint', '').lower()
    if hint == 'ignore':
        LOGGER.debug("Ignoring email due to 'ignore' hint")
        return

    if list_id:
        project = find_project_by_id(list_id)
    else:
        project = find_project_by_header(mail)

    if project is None:
        LOGGER.error('Failed to find a project for email')
        return

    # parse content

    diff, message = find_content(project, mail)

    if not (diff or message):
        return  # nothing to work with

    msgid = mail.get('Message-Id').strip()
    author = find_author(mail)
    name, prefixes = clean_subject(mail.get('Subject'), [project.linkname])
    x, n = parse_series_marker(prefixes)
    refs = find_references(mail)
    date = find_date(mail)
    headers = find_headers(mail)
    pull_url = parse_pull_request(message)

    # build objects

    if diff or pull_url:  # patches or pull requests
        # we delay the saving until we know we have a patch.
        author.save()

        delegate = find_delegate(mail)
        if not delegate and diff:
            filenames = find_filenames(diff)
            delegate = auto_delegate(project, filenames)

        patch = Patch(
            msgid=msgid,
            project=project,
            name=name,
            date=date,
            headers=headers,
            submitter=author,
            content=message,
            diff=diff,
            pull_url=pull_url,
            delegate=delegate,
            state=find_state(mail))
        patch.save()
        LOGGER.debug('Patch saved')

        return patch
    elif x == 0:  # (potential) cover letters
        # if refs are empty, it's implicitly a cover letter. If not,
        # however, we need to see if a match already exists and, if
        # not, assume that it is indeed a new cover letter
        is_cover_letter = False
        if not refs == []:
            try:
                CoverLetter.objects.all().get(name=name)
            except CoverLetter.DoesNotExist:
                # if no match, this is a new cover letter
                is_cover_letter = True
            except CoverLetter.MultipleObjectsReturned:
                # if multiple cover letters are found, just ignore
                pass
        else:
            is_cover_letter = True

        if is_cover_letter:
            author.save()

            cover_letter = CoverLetter(
                msgid=msgid,
                project=project,
                name=name,
                date=date,
                headers=headers,
                submitter=author,
                content=message)
            cover_letter.save()
            LOGGER.debug('Cover letter saved')

            return cover_letter

    # comments

    # we only save comments if we have the parent email
    submission = find_submission_for_comment(project, refs)
    if not submission:
        return

    author.save()

    comment = Comment(
        submission=submission,
        msgid=msgid,
        date=date,
        headers=headers,
        submitter=author,
        content=message)
    comment.save()
    LOGGER.debug('Comment saved')

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
