# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import datetime
from email.encoders import encode_7or8bit
from email.header import Header
from email.mime.nonmultipart import MIMENonMultipart
from email.parser import HeaderParser
import email.utils
import re

from django.conf import settings
from django.http import Http404
from django.utils import six

from patchwork.models import Comment
from patchwork.models import Patch

if settings.ENABLE_REST_API:
    from rest_framework.authtoken.models import Token


class PatchMbox(MIMENonMultipart):
    patch_charset = 'utf-8'

    def __init__(self, _text):
        MIMENonMultipart.__init__(self, 'text', 'plain',
                                  **{'charset': self.patch_charset})
        self.set_payload(_text.encode(self.patch_charset))
        encode_7or8bit(self)


def _submission_to_mbox(submission):
    """Get an mbox representation of a single Submission.

    Handles both Patch and CoverLetter objects.

    Arguments:
        submission: The Patch object to convert.

    Returns:
        A string for the mbox file.
    """
    is_patch = isinstance(submission, Patch)

    postscript_re = re.compile('\n-{2,3} ?\n')
    body = ''

    if submission.content:
        body = submission.content.strip() + "\n"

    parts = postscript_re.split(body, 1)
    if len(parts) == 2:
        (body, postscript) = parts
        body = body.strip() + "\n"
        postscript = postscript.rstrip()
    else:
        postscript = ''

    # TODO(stephenfin): Make this use the tags infrastructure
    for comment in Comment.objects.filter(submission=submission):
        body += comment.patch_responses

    if postscript:
        body += '---\n' + postscript + '\n'

    if is_patch and submission.diff:
        body += '\n' + submission.diff

    delta = submission.date - datetime.datetime.utcfromtimestamp(0)
    utc_timestamp = delta.seconds + delta.days * 24 * 3600

    mail = PatchMbox(body)
    mail['X-Patchwork-Submitter'] = email.utils.formataddr((
        str(Header(submission.submitter.name, mail.patch_charset)),
        submission.submitter.email))
    mail['X-Patchwork-Id'] = str(submission.id)
    if is_patch and submission.delegate:
        mail['X-Patchwork-Delegate'] = str(submission.delegate.email)
    mail.set_unixfrom('From patchwork ' + submission.date.ctime())

    orig_headers = HeaderParser().parsestr(str(submission.headers))
    for key, val in orig_headers.items():
        if key == 'Content-Transfer-Encoding':
            continue
        mail[key] = val

    if 'Date' not in mail:
        mail['Date'] = email.utils.formatdate(utc_timestamp)

    # NOTE(stephenfin) http://stackoverflow.com/a/28584090/613428
    if six.PY3:
        mail = mail.as_bytes(True).decode()
    else:
        mail = mail.as_string(True)

    return mail


patch_to_mbox = _submission_to_mbox
cover_to_mbox = _submission_to_mbox


def bundle_to_mbox(bundle):
    """Get an mbox representation of a bundle.

    Arguments:
        patch: The Bundle object to convert.

    Returns:
        A string for the mbox file.
    """
    return '\n'.join([patch_to_mbox(p) for p in bundle.ordered_patches()])


def series_patch_to_mbox(patch, series_id):
    """Get an mbox representation of a patch with dependencies.

    Arguments:
        patch: The Patch object to convert.
        series_id: The series number to retrieve dependencies from, or
            '*' if using the latest series.

    Returns:
        A string for the mbox file.
    """
    if series_id != '*':
        try:
            series_id = int(series_id)
        except ValueError:
            raise Http404('Expected integer series value or *. Received: %r' %
                          series_id)

        if patch.series.id != series_id:
            raise Http404('Patch does not belong to series %d' % series_id)

    mbox = []

    # get the series-ified patch
    for dep in patch.series.patches.filter(
            number__lt=patch.number).order_by('number'):
        mbox.append(patch_to_mbox(dep))

    mbox.append(patch_to_mbox(patch))

    return '\n'.join(mbox)


def series_to_mbox(series):
    """Get an mbox representation of an entire series.

    Arguments:
        series: The Series object to convert.

    Returns:
        A string for the mbox file.
    """
    mbox = []

    for dep in series.patches.all().order_by('number'):
        mbox.append(patch_to_mbox(dep.patch))

    return '\n'.join(mbox)


def regenerate_token(user):
    """Generate (or regenerate) user API tokens.

    Arguments:
        user: The User object to generate a token for.
    """
    Token.objects.filter(user=user).delete()
    Token.objects.create(user=user)
