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

from __future__ import absolute_import

import argparse
import codecs
import datetime
from email import message_from_file
from email.header import decode_header, make_header
from email.utils import parsedate_tz, mktime_tz
from fnmatch import fnmatch
import logging
import re
import sys

import django
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.log import AdminEmailHandler
from django.utils import six

from patchwork.models import (Patch, Project, Person, Comment, State,
                              DelegationRule, get_default_initial_patch_state)
from patchwork.parser import parse_patch, patch_get_filenames

LOGGER = logging.getLogger(__name__)

VERBOSITY_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

list_id_headers = ['List-ID', 'X-Mailing-List', 'X-list']


def normalise_space(str):
    whitespace_re = re.compile(r'\s+')
    return whitespace_re.sub(' ', str).strip()


def sanitise_header(header_contents, header_name=None):
    """Clean and individual mail header.

    Given a header with header_contents, optionally labelled
    header_name, decode it with decode_header, sanitise it to make
    sure it decodes correctly and contains no invalid characters,
    then encode the result with make_header()
    """

    # We have some Py2/Py3 issues here.
    #
    # Firstly, the email parser (before we get here)
    # Python 3: headers with weird chars are email.header.Header
    #           class, others as str
    # Python 2: every header is an str
    #
    # Secondly, the behaviour of decode_header:
    # Python 3: weird headers are labelled as unknown-8bit
    # Python 2: weird headers are not labelled differently
    #
    # Lastly, aking matters worse, in Python2, unknown-8bit doesn't
    # seem to be supported as an input to make_header, so not only do
    # we have to detect dodgy headers, we have to fix them ourselves.
    #
    # We solve this by catching any Unicode errors, and then manually
    # handling any interesting headers.

    value = decode_header(header_contents)
    try:
        header = make_header(value,
                             header_name=header_name,
                             continuation_ws='\t')
    except UnicodeDecodeError:
        # At least one of the parts cannot be encoded as ascii.
        # Find out which one and fix it somehow.
        #
        # We get here under Py2 when there's non-7-bit chars in header,
        # or under Py2 or Py3 where decoding with the coding hint fails.

        new_value = []

        for (part, coding) in value:
            # We have random bytes that aren't properly coded.
            # If we had a coding hint, it failed to help.
            if six.PY3:
                # python3 - force coding to unknown-8bit
                new_value += [(part, 'unknown-8bit')]
            else:
                # python2 - no support in make_header for unknown-8bit
                # We should do unknown-8bit coding ourselves.
                # For now, we're just going to replace any dubious
                # chars with ?.
                #
                # TODO: replace it with a proper QP unknown-8bit codec.
                new_value += [(part.decode('ascii', errors='replace')
                               .encode('ascii', errors='replace'),
                               None)]

        header = make_header(new_value,
                             header_name=header_name,
                             continuation_ws='\t')

    return header


def clean_header(header):
    """Decode (possibly non-ascii) headers."""

    sane_header = sanitise_header(header)

    # on Py2, we want to do unicode(), on Py3, str().
    # That gets us the decoded, un-wrapped header.
    if six.PY2:
        header_str = unicode(sane_header)
    else:
        header_str = str(sane_header)

    return normalise_space(header_str)


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
    (name, email) = (None, None)

    # tuple of (regex, fn)
    #  - where fn returns a (name, email) tuple from the match groups resulting
    #    from re.match().groups()
    from_res = [
        # for "Firstname Lastname" <example@example.com> style addresses
        (re.compile(r'"?(.*?)"?\s*<([^>]+)>'), (lambda g: (g[0], g[1]))),

        # for example@example.com (Firstname Lastname) style addresses
        (re.compile(r'"?(.*?)"?\s*\(([^\)]+)\)'), (lambda g: (g[1], g[0]))),

        # for example at example.com (Firstname Lastname) style addresses
        (re.compile(r'(.*?)\sat\s(.*?)\s*\(([^\)]+)\)'),
         (lambda g: (g[2], '@'.join(g[0:2])))),

        # everything else
        (re.compile(r'(.*)'), (lambda g: (None, g[0]))),
    ]

    for regex, fn in from_res:
        match = regex.match(from_header)
        if match:
            (name, email) = fn(match.groups())
            break

    if email is None:
        raise Exception("Could not parse From: header")

    email = email.strip()
    if name is not None:
        name = name.strip()

    new_person = False

    try:
        person = Person.objects.get(email__iexact=email)
    except Person.DoesNotExist:
        person = Person(name=name, email=email)
        new_person = True

    return (person, new_person)


def mail_date(mail):
    t = parsedate_tz(mail.get('Date', ''))
    if not t:
        return datetime.datetime.utcnow()
    return datetime.datetime.utcfromtimestamp(mktime_tz(t))


def mail_headers(mail):
    headers = [(key, sanitise_header(value, header_name=key))
               for key, value in mail.items()]

    strings = [('%s: %s' % (key, header.encode()))
               for (key, header) in headers]

    return '\n'.join(strings)


def find_pull_request(content):
    git_re = re.compile(r'^The following changes since commit.*' +
                        r'^are available in the git repository at:\n'
                        r'^\s*([\S]+://[^\n]+)$',
                        re.DOTALL | re.MULTILINE)
    match = git_re.search(content)
    if match:
        return match.group(1)
    return None


def try_decode(payload, charset):
    try:
        payload = six.text_type(payload, charset)
    except UnicodeDecodeError:
        return None
    return payload


def find_content(project, mail):
    patchbuf = None
    commentbuf = ''
    pullurl = None

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
                decoded_payload = try_decode(payload, cset)
                if decoded_payload is not None:
                    break
            payload = decoded_payload

            # Could not find a valid decoded payload.  Fail.
            if payload is None:
                return (None, None, None)

        if subtype in ['x-patch', 'x-diff']:
            patchbuf = payload

        elif subtype == 'plain':
            c = payload

            if not patchbuf:
                (patchbuf, c) = parse_patch(payload)

            if not pullurl:
                pullurl = find_pull_request(payload)

            if c is not None:
                commentbuf += c.strip() + '\n'

    patch = None
    comment = None
    filenames = None

    if patchbuf:
        filenames = patch_get_filenames(patchbuf)

    if pullurl or patchbuf:
        name = clean_subject(mail.get('Subject'), [project.linkname])
        patch = Patch(name=name, pull_url=pullurl, content=patchbuf,
                      date=mail_date(mail), headers=mail_headers(mail))

    if commentbuf:
        # If this is a new patch, we defer setting comment.patch until
        # patch has been saved by the caller
        if patch:
            comment = Comment(date=mail_date(mail),
                              content=clean_content(commentbuf),
                              headers=mail_headers(mail))
        else:
            cpatch = find_patch_for_comment(project, mail)
            if not cpatch:
                return (None, None, None)
            comment = Comment(patch=cpatch, date=mail_date(mail),
                              content=clean_content(commentbuf),
                              headers=mail_headers(mail))

    return (patch, comment, filenames)


def find_patch_for_comment(project, mail):
    # construct a list of possible reply message ids
    refs = []
    if 'In-Reply-To' in mail:
        refs.append(mail.get('In-Reply-To'))

    if 'References' in mail:
        rs = mail.get('References').split()
        rs.reverse()
        for r in rs:
            if r not in refs:
                refs.append(r)

    for ref in refs:
        patch = None

        # first, check for a direct reply
        try:
            patch = Patch.objects.get(project=project, msgid=ref)
            return patch
        except Patch.DoesNotExist:
            pass

        # see if we have comments that refer to a patch
        try:
            comment = Comment.objects.get(patch__project=project, msgid=ref)
            return comment.patch
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

    return subject


def clean_content(content):
    """Remove cruft from the email message.

    Catch ignature (-- ) and list footer (_____) cruft.
    """
    sig_re = re.compile(r'^(-- |_+)\n.*', re.S | re.M)
    content = sig_re.sub('', content)

    return content.strip()


def get_state(state_name):
    """Return the state with the given name or the default."""
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


def get_delegate(delegate_email):
    """Return the delegate with the given email or None."""
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
        LOGGER.debug("Ignoring patch due to missing 'From'")
        return 1

    if 'Subject' not in mail:
        LOGGER.debug("Ignoring patch due to missing 'Subject'")
        return 1

    if 'Message-Id' not in mail:
        LOGGER.debug("Ignoring patch due to missing 'Message-Id'")
        return 1

    hint = mail.get('X-Patchwork-Hint', '').lower()
    if hint == 'ignore':
        LOGGER.debug("Ignoring patch due to 'ignore' hint")
        return 0

    if list_id:
        project = find_project_by_id(list_id)
    else:
        project = find_project_by_header(mail)

    if project is None:
        LOGGER.error('Failed to find a project for patch')
        return 1

    msgid = mail.get('Message-Id').strip()

    (author, save_required) = find_author(mail)

    (patch, comment, filenames) = find_content(project, mail)

    if patch:
        delegate = get_delegate(mail.get('X-Patchwork-Delegate', '').strip())
        if not delegate:
            delegate = auto_delegate(project, filenames)

        # we delay the saving until we know we have a patch.
        if save_required:
            author.save()
            save_required = False
        patch.submitter = author
        patch.msgid = msgid
        patch.project = project
        patch.state = get_state(mail.get('X-Patchwork-State', '').strip())
        patch.delegate = get_delegate(
            mail.get('X-Patchwork-Delegate', '').strip())
        patch.save()
        LOGGER.debug('Patch saved')

    if comment:
        if save_required:
            author.save()
        # we defer this assignment until we know that we have a saved patch
        if patch:
            comment.patch = patch
        comment.submitter = author
        comment.msgid = msgid
        comment.save()
        LOGGER.debug('Comment saved')

    return 0

extra_error_message = '''
== Mail

%(mail)s


== Traceback

'''


def setup_error_handler():
    """Configure error handler.

    Ensure emails are send to settings.ADMINS when errors are
    encountered.
    """
    if settings.DEBUG:
        return

    mail_handler = AdminEmailHandler()
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(extra_error_message))

    logger = logging.getLogger('patchwork')
    logger.addHandler(mail_handler)

    return logger


def main(args):
    django.setup()
    logger = setup_error_handler()
    parser = argparse.ArgumentParser()

    def list_logging_levels():
        """Give a summary of all available logging levels."""
        return sorted(list(VERBOSITY_LEVELS.keys()),
                      key=lambda x: VERBOSITY_LEVELS[x])

    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help='input mbox file (a filename '
                        'or stdin)')

    group = parser.add_argument_group('Mail parsing configuration')
    group.add_argument('--list-id', help='mailing list ID. If not supplied '
                       'this will be extracted from the mail headers.')
    group.add_argument('--verbosity', choices=list_logging_levels(),
                       help='debug level', default='info')

    args = vars(parser.parse_args())

    logging.basicConfig(level=VERBOSITY_LEVELS[args['verbosity']])

    mail = message_from_file(args['infile'])
    try:
        return parse_mail(mail, args['list_id'])
    except:
        if logger:
            logger.exception('Error when parsing incoming email', extra={
                'mail': mail.as_string(),
            })
        raise
    return parse_mail(mail, args['list_id'])

if __name__ == '__main__':
    sys.exit(main(sys.argv))
