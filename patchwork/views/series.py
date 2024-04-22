# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import collections

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.models import Series
from patchwork.models import Project
from patchwork.views.utils import series_to_mbox
from patchwork.paginator import Paginator


def series_mbox(request, series_id):
    series = get_object_or_404(Series, id=series_id)

    response = HttpResponse(content_type='text/plain')
    response.write(series_to_mbox(series))
    response['Content-Disposition'] = 'attachment; filename=%s.patch' % (
        series.filename
    )

    return response


def series_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)
    sort = request.GET.get('order', 'date.desc')
    sort_field, sort_dir = sort.split('.')
    sort_order = f"{'-' if sort_dir == 'desc' else ''}{sort_field}"
    context = {}
    series_list = (
        Series.objects.filter(project=project)
        .only(
            'submitter',
            'project',
            'version',
            'name',
            'date',
            'id',
            'cover_letter',
        )
        .select_related('project', 'submitter', 'cover_letter')
        .order_by(sort_order)
    )

    paginator = Paginator(request, series_list)
    context.update(
        {
            'project': project,
            'projects': Project.objects.all(),
            'series_list': series_list,
            'page': paginator.current_page,
            'order': sort,
            'list_view': {
                'view': 'series-list',
                'view_params': {'project_id': project.linkname},
                'params': collections.OrderedDict(),
            },
        }
    )

    return render(request, 'patchwork/series-list.html', context)
