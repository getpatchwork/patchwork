# Patchwork - automated patch tracking system
# Copyright (C) 2016 Linaro Corporation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class IndexView(APIView):

    def get(self, request, *args, **kwargs):
        """List API resources."""
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
