# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
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

import datetime
from email.encoders import encode_7or8bit
from email.header import Header
from email.mime.nonmultipart import MIMENonMultipart
from email.parser import HeaderParser
import email.utils
import re

from django.http import Http404
from django.utils import six

from patchwork.models import Comment
from patchwork.models import Series


class PatchMbox(MIMENonMultipart):
    patch_charset = 'utf-8'

    def __init__(self, _text):
        MIMENonMultipart.__init__(self, 'text', 'plain',
                                  **{'charset': self.patch_charset})
        self.set_payload(_text.encode(self.patch_charset))
        encode_7or8bit(self)


def patch_to_mbox(patch):
    """Get an mbox representation of a single patch.

    Arguments:
        patch: The Patch object to convert.

    Returns:
        A string for the mbox file.
    """
    postscript_re = re.compile('\n-{2,3} ?\n')
    body = ''

    if patch.content:
        body = patch.content.strip() + "\n"

    parts = postscript_re.split(body, 1)
    if len(parts) == 2:
        (body, postscript) = parts
        body = body.strip() + "\n"
        postscript = postscript.rstrip()
    else:
        postscript = ''

    # TODO(stephenfin): Make this use the tags infrastructure
    for comment in Comment.objects.filter(submission=patch):
        body += comment.patch_responses

    if postscript:
        body += '---\n' + postscript + '\n'

    if patch.diff:
        body += '\n' + patch.diff

    delta = patch.date - datetime.datetime.utcfromtimestamp(0)
    utc_timestamp = delta.seconds + delta.days * 24 * 3600

    mail = PatchMbox(body)
    mail['Subject'] = patch.name
    mail['X-Patchwork-Submitter'] = email.utils.formataddr((
        str(Header(patch.submitter.name, mail.patch_charset)),
        patch.submitter.email))
    mail['X-Patchwork-Id'] = str(patch.id)
    if patch.delegate:
        mail['X-Patchwork-Delegate'] = str(patch.delegate.email)
    mail['Message-Id'] = patch.msgid
    mail.set_unixfrom('From patchwork ' + patch.date.ctime())

    copied_headers = ['To', 'Cc', 'Date', 'From', 'List-Id']
    orig_headers = HeaderParser().parsestr(str(patch.headers))
    for header in copied_headers:
        if header in orig_headers:
            mail[header] = orig_headers[header]

    if 'Date' not in mail:
        mail['Date'] = email.utils.formatdate(utc_timestamp)

    # NOTE(stephenfin) http://stackoverflow.com/a/28584090/613428
    if six.PY3:
        mail = mail.as_bytes(True).decode()
    else:
        mail = mail.as_string(True)

    return mail


def bundle_to_mbox(bundle):
    """Get an mbox representation of a bundle.

    Arguments:
        patch: The Bundle object to convert.

    Returns:
        A string for the mbox file.
    """
    return '\n'.join([patch_to_mbox(p) for p in bundle.ordered_patches()])


def series_patch_to_mbox(patch, series_num):
    """Get an mbox representation of a patch with dependencies.

    Arguments:
        patch: The Patch object to convert.
        series_num: The series number to retrieve dependencies from.

    Returns:
        A string for the mbox file.
    """
    try:
        series_num = int(series_num)
    except ValueError:
        raise Http404('Expected integer series value. Received: %r' %
                      series_num)

    try:
        series = patch.series.get(id=series_num)
    except Series.DoesNotExist:
        raise Http404('Patch does not belong to series %d' % series_num)

    mbox = []

    # get the series-ified patch
    number = series.seriespatch_set.get(patch=patch).number
    for dep in series.seriespatch_set.filter(number__lt=number):
        mbox.append(patch_to_mbox(dep.patch))

    mbox.append(patch_to_mbox(patch))

    return '\n'.join(mbox)
