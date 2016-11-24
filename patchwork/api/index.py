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

from django.core.urlresolvers import reverse
from rest_framework.response import Response
from rest_framework.views import APIView


class IndexView(APIView):

    def get(self, request, format=None):
        return Response({
            'projects': request.build_absolute_uri(
                reverse('api-project-list')),
            'users': request.build_absolute_uri(reverse('api-user-list')),
            'people': request.build_absolute_uri(reverse('api-person-list')),
            'patches': request.build_absolute_uri(reverse('api-patch-list')),
            'covers': request.build_absolute_uri(reverse('api-cover-list')),
            'series': request.build_absolute_uri(reverse('api-series-list')),
        })
