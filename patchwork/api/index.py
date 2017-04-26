# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
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

from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class IndexView(APIView):

    def get(self, request, *args, **kwargs):
        return Response({
            'projects': reverse('api-project-list', request=request),
            'users': reverse('api-user-list', request=request),
            'people': reverse('api-person-list', request=request),
            'patches': reverse('api-patch-list', request=request),
            'covers': reverse('api-cover-list', request=request),
            'series': reverse('api-series-list', request=request),
            'events': reverse('api-event-list', request=request),
            'bundles': reverse('api-bundle-list', request=request),
        })
