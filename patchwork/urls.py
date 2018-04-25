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

import django
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from patchwork.compat import reverse_lazy
from patchwork.views import about as about_views
from patchwork.views import api as api_views
from patchwork.views import bundle as bundle_views
from patchwork.views import comment as comment_views
from patchwork.views import cover as cover_views
from patchwork.views import mail as mail_views
from patchwork.views import notification as notification_views
from patchwork.views import patch as patch_views
from patchwork.views import project as project_views
from patchwork.views import pwclient as pwclient_views
from patchwork.views import series as series_views
from patchwork.views import user as user_views
from patchwork.views import xmlrpc as xmlrpc_views


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', project_views.project_list, name='project-list'),
    url(r'^project/(?P<project_id>[^/]+)/list/$', patch_views.patch_list,
        name='patch-list'),
    url(r'^project/(?P<project_id>[^/]+)/bundles/$', bundle_views.bundle_list,
        name='bundle-list'),
    url(r'^project/(?P<project_id>[^/]+)/$', project_views.project_detail,
        name='project-detail'),

    # patch views
    url(r'^patch/(?P<patch_id>\d+)/$', patch_views.patch_detail,
        name='patch-detail'),
    url(r'^patch/(?P<patch_id>\d+)/raw/$', patch_views.patch_raw,
        name='patch-raw'),
    url(r'^patch/(?P<patch_id>\d+)/mbox/$', patch_views.patch_mbox,
        name='patch-mbox'),

    # cover views
    url(r'^cover/(?P<cover_id>\d+)/$', cover_views.cover_detail,
        name='cover-detail'),
    url(r'^cover/(?P<cover_id>\d+)/mbox/$', cover_views.cover_mbox,
        name='cover-mbox'),

    # comment views
    url(r'^comment/(?P<comment_id>\d+)/$', comment_views.comment,
        name='comment-redirect'),

    # series views
    url(r'^series/(?P<series_id>\d+)/mbox/$', series_views.series_mbox,
        name='series-mbox'),

    # logged-in user stuff
    url(r'^user/$', user_views.profile, name='user-profile'),
    url(r'^user/todo/$', user_views.todo_lists,
        name='user-todos'),
    url(r'^user/todo/(?P<project_id>[^/]+)/$', user_views.todo_list,
        name='user-todo'),
    url(r'^user/bundles/$', bundle_views.bundle_list,
        name='user-bundles'),

    url(r'^user/link/$', user_views.link,
        name='user-link'),
    url(r'^user/unlink/(?P<person_id>[^/]+)/$', user_views.unlink,
        name='user-unlink'),
]

# password change
if django.VERSION >= (1, 11):
    urlpatterns += [
        url(r'^user/password-change/$',
            auth_views.PasswordChangeView.as_view(),
            name='password_change'),
        url(r'^user/password-change/done/$',
            auth_views.PasswordChangeDoneView.as_view(),
            name='password_change_done'),
        url(r'^user/password-reset/$',
            auth_views.PasswordResetView.as_view(),
            name='password_reset'),
        url(r'^user/password-reset/mail-sent/$',
            auth_views.PasswordResetDoneView.as_view(),
            name='password_reset_done'),
        url(r'^user/password-reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
            r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            auth_views.PasswordResetConfirmView.as_view(),
            name='password_reset_confirm'),
        url(r'^user/password-reset/complete/$',
            auth_views.PasswordResetCompleteView.as_view(),
            name='password_reset_complete'),
    ]
else:
    urlpatterns += [
        url(r'^user/password-change/$',
            auth_views.password_change,
            name='password_change'),
        url(r'^user/password-change/done/$',
            auth_views.password_change_done,
            name='password_change_done'),
        url(r'^user/password-reset/$',
            auth_views.password_reset,
            name='password_reset'),
        url(r'^user/password-reset/mail-sent/$',
            auth_views.password_reset_done,
            name='password_reset_done'),
        url(r'^user/password-reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
            r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
            auth_views.password_reset_confirm,
            name='password_reset_confirm'),
        url(r'^user/password-reset/complete/$',
            auth_views.password_reset_complete,
            name='password_reset_complete'),
    ]

# login/logout
if django.VERSION >= (1, 11):
    urlpatterns += [
        url(r'^user/login/$', auth_views.LoginView.as_view(
            template_name='patchwork/login.html'),
            name='auth_login'),
        url(r'^user/logout/$', auth_views.LogoutView.as_view(
            next_page=reverse_lazy('project-list')),
            name='auth_logout'),
    ]
else:
    urlpatterns += [
        url(r'^user/login/$', auth_views.login,
            {'template_name': 'patchwork/login.html'},
            name='auth_login'),
        url(r'^user/logout/$', auth_views.logout,
            {'next_page': reverse_lazy('project-list')},
            name='auth_logout'),
    ]

urlpatterns += [
    # registration
    url(r'^register/', user_views.register, name='user-register'),

    # public view for bundles
    url(r'^bundle/(?P<username>[^/]*)/(?P<bundlename>[^/]*)/$',
        bundle_views.bundle_detail,
        name='bundle-detail'),
    url(r'^bundle/(?P<username>[^/]*)/(?P<bundlename>[^/]*)/mbox/$',
        bundle_views.bundle_mbox,
        name='bundle-mbox'),

    url(r'^confirm/(?P<key>[0-9a-f]+)/$', notification_views.confirm,
        name='confirm'),

    # submitter autocomplete
    url(r'^submitter/$', api_views.submitters, name='api-submitters'),
    url(r'^delegate/$', api_views.delegates, name='api-delegates'),

    # email setup
    url(r'^mail/$', mail_views.settings, name='mail-settings'),
    url(r'^mail/optout/$', mail_views.optout, name='mail-optout'),
    url(r'^mail/optin/$', mail_views.optin, name='mail-optin'),

    # about
    url(r'^about/$', about_views.about, name='about'),

    # legacy redirects
    url(r'^help/$', about_views.redirect, name='help'),
    url(r'^help/about/$', about_views.redirect, name='help-about'),
]

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar  # noqa

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

if settings.ENABLE_XMLRPC:
    urlpatterns += [
        url(r'xmlrpc/$', xmlrpc_views.xmlrpc, name='xmlrpc'),
        url(r'^pwclient/$', pwclient_views.pwclient,
            name='pwclient'),
        url(r'^project/(?P<project_id>[^/]+)/pwclientrc/$',
            pwclient_views.pwclientrc,
            name='pwclientrc'),
        # legacy redirect
        url(r'^help/pwclient/$', about_views.redirect, name='help-pwclient'),
    ]

if settings.ENABLE_REST_API:
    if 'rest_framework' not in settings.INSTALLED_APPS:
        raise RuntimeError(
            'djangorestframework must be installed to enable the REST API.')

    from patchwork.api import bundle as api_bundle_views  # noqa
    from patchwork.api import check as api_check_views  # noqa
    from patchwork.api import comment as api_comment_views  # noqa
    from patchwork.api import cover as api_cover_views  # noqa
    from patchwork.api import event as api_event_views  # noqa
    from patchwork.api import index as api_index_views  # noqa
    from patchwork.api import patch as api_patch_views  # noqa
    from patchwork.api import person as api_person_views  # noqa
    from patchwork.api import project as api_project_views  # noqa
    from patchwork.api import series as api_series_views  # noqa
    from patchwork.api import user as api_user_views  # noqa

    api_patterns = [
        url(r'^$',
            api_index_views.IndexView.as_view(),
            name='api-index'),
        url(r'^users/$',
            api_user_views.UserList.as_view(),
            name='api-user-list'),
        url(r'^users/(?P<pk>[^/]+)/$',
            api_user_views.UserDetail.as_view(),
            name='api-user-detail'),
        url(r'^people/$',
            api_person_views.PersonList.as_view(),
            name='api-person-list'),
        url(r'^people/(?P<pk>[^/]+)/$',
            api_person_views.PersonDetail.as_view(),
            name='api-person-detail'),
        url(r'^covers/$',
            api_cover_views.CoverLetterList.as_view(),
            name='api-cover-list'),
        url(r'^covers/(?P<pk>[^/]+)/$',
            api_cover_views.CoverLetterDetail.as_view(),
            name='api-cover-detail'),
        url(r'^patches/$',
            api_patch_views.PatchList.as_view(),
            name='api-patch-list'),
        url(r'^patches/(?P<pk>[^/]+)/$',
            api_patch_views.PatchDetail.as_view(),
            name='api-patch-detail'),
        url(r'^patches/(?P<patch_id>[^/]+)/checks/$',
            api_check_views.CheckListCreate.as_view(),
            name='api-check-list'),
        url(r'^patches/(?P<patch_id>[^/]+)/checks/(?P<check_id>[^/]+)/$',
            api_check_views.CheckDetail.as_view(),
            name='api-check-detail'),
        url(r'^series/$',
            api_series_views.SeriesList.as_view(),
            name='api-series-list'),
        url(r'^series/(?P<pk>[^/]+)/$',
            api_series_views.SeriesDetail.as_view(),
            name='api-series-detail'),
        url(r'^bundles/$',
            api_bundle_views.BundleList.as_view(),
            name='api-bundle-list'),
        url(r'^bundles/(?P<pk>[^/]+)/$',
            api_bundle_views.BundleDetail.as_view(),
            name='api-bundle-detail'),
        url(r'^projects/$',
            api_project_views.ProjectList.as_view(),
            name='api-project-list'),
        url(r'^projects/(?P<pk>[^/]+)/$',
            api_project_views.ProjectDetail.as_view(),
            name='api-project-detail'),
        url(r'^events/$',
            api_event_views.EventList.as_view(),
            name='api-event-list'),
    ]

    api_1_1_patterns = [
        url(r'^patches/(?P<pk>[^/]+)/comments/$',
            api_comment_views.CommentList.as_view(),
            name='api-comment-list'),
        url(r'^covers/(?P<pk>[^/]+)/comments/$',
            api_comment_views.CommentList.as_view(),
            name='api-comment-list'),
    ]

    urlpatterns += [
        url(r'^api/(?:(?P<version>(1.0|1.1))/)?', include(api_patterns)),
        url(r'^api/(?:(?P<version>1.1)/)?', include(api_1_1_patterns)),

        # token change
        url(r'^user/generate-token/$', user_views.generate_token,
            name='generate_token'),
    ]


# redirect from old urls
if settings.COMPAT_REDIR:
    urlpatterns += [
        url(r'^user/bundle/(?P<bundle_id>[^/]+)/$',
            bundle_views.bundle_detail_redir,
            name='bundle-redir'),
        url(r'^user/bundle/(?P<bundle_id>[^/]+)/mbox/$',
            bundle_views.bundle_mbox_redir,
            name='bundle-mbox-redir'),
    ]
