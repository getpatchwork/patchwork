# Patchwork - automated patch tracking system
# Copyright (C) 2016 Stephen Finucane <stephen@that.guru>
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

from django import http
from django import shortcuts

from patchwork.compat import reverse
from patchwork import models


def comment(request, comment_id):
    submission = shortcuts.get_object_or_404(models.Comment,
                                             id=comment_id).submission
    if models.Patch.objects.filter(id=submission.id).exists():
        url = 'patch-detail'
        key = 'patch_id'
    else:
        url = 'cover-detail'
        key = 'cover_id'

    return http.HttpResponseRedirect('%s#%s' % (
        reverse(url, kwargs={key: submission.id}), comment_id))
