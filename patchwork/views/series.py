# Patchwork - automated patch tracking system
# Copyright (C) 2017 Stephen Finucane <stephen@that.guru>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from patchwork.models import Series
from patchwork.models import Patch
from patchwork.models import Project
from patchwork.views import generic_list
from patchwork.views.utils import series_to_mbox
from patchwork.forms import SeriesBulkUpdatePatchesForm


def series_mbox(request, series_id):
    series = get_object_or_404(Series, id=series_id)

    response = HttpResponse(content_type='text/plain')
    response.write(series_to_mbox(series))
    response['Content-Disposition'] = 'attachment; filename=%s.patch' % (
        series.filename
    )

    return response


def series_detail(request, series_id):
    series = get_object_or_404(Series, id=series_id)

    patches = Patch.objects.filter(series=series)

    context = generic_list(
        request,
        series.project,
        'series-detail',
        view_args={'series_id': series_id},
        patches=patches,
    )

    context.update({'series': series})

    return render(request, 'patchwork/series-detail.html', context)


def series_list(request, project_id):
    project = get_object_or_404(Project, linkname=project_id)

    form = SeriesBulkUpdatePatchesForm(project)
    context = {}

    if request.method == 'POST':
        form = SeriesBulkUpdatePatchesForm(project, request.POST)
        errors = _update_series_patches(request, form)
        if len(errors) > 0:
            context.update({'errors': errors})
    else:
        form = SeriesBulkUpdatePatchesForm(project)

    series_list = (
        Series.objects.filter(project=project)
        .only(
            'submitter',
            'project',
            'version',
            'name',
            'date',
            'id',
        )
        .select_related('project')
    )

    context.update(
        {
            'project': project,
            'projects': Project.objects.all(),
            'series_list': series_list,
            'form': form,
        }
    )

    return render(request, 'patchwork/series-list.html', context)


def _update_series_patches(request, form):
    pk = request.POST.get('save')
    series = Series.objects.get(id=pk)

    if not form.is_valid():
        errors = ['The submitted form data was invalid']
        for field_name, error_message in form.errors.items():
            errors.append(f'{field_name}: {error_message}')

        return errors

    return form.save(series, request)
