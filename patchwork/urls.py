# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, re_path, reverse_lazy

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
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^$', project_views.project_list, name='project-list'),
    re_path(
        r'^project/(?P<project_id>[^/]+)/list/$',
        patch_views.patch_list,
        name='patch-list',
    ),
    re_path(
        r'^project/(?P<project_id>[^/]+)/bundles/$',
        bundle_views.bundle_list,
        name='bundle-list',
    ),
    re_path(
        r'^project/(?P<project_id>[^/]+)/$',
        project_views.project_detail,
        name='project-detail',
    ),
    # patch views
    # NOTE(dja): Per the RFC, msgids can contain slashes. There doesn't seem
    # to be an easy way to tell Django to urlencode the slash when generating
    # URLs, so instead we must use a permissive regex (.+ rather than [^/]+).
    # This also means we need to put the raw and mbox URLs first, otherwise the
    # patch-detail regex will just greedily grab those parts into a massive and
    # wrong msgid.
    #
    # This does mean that message-ids that end in '/raw/' or '/mbox/' will not
    # work, but it is RECOMMENDED by the RFC that the right hand side of the @
    # contains a domain, so I think breaking on messages that have "domains"
    # ending in /raw/ or /mbox/ is good enough.
    re_path(
        r'^project/(?P<project_id>[^/]+)/patch/(?P<msgid>.+)/raw/$',
        patch_views.patch_raw,
        name='patch-raw',
    ),
    re_path(
        r'^project/(?P<project_id>[^/]+)/patch/(?P<msgid>.+)/mbox/$',
        patch_views.patch_mbox,
        name='patch-mbox',
    ),
    re_path(
        r'^project/(?P<project_id>[^/]+)/patch/(?P<msgid>.+)/$',
        patch_views.patch_detail,
        name='patch-detail',
    ),
    # ... old-style /patch/N/* urls
    re_path(
        r'^patch/(?P<patch_id>\d+)/raw/$',
        patch_views.patch_raw_by_id,
        name='patch-raw-redirect',
    ),
    re_path(
        r'^patch/(?P<patch_id>\d+)/mbox/$',
        patch_views.patch_mbox_by_id,
        name='patch-mbox-redirect',
    ),
    re_path(
        r'^patch/(?P<patch_id>\d+)/$',
        patch_views.patch_by_id,
        name='patch-id-redirect',
    ),
    # cover views
    re_path(
        r'^project/(?P<project_id>[^/]+)/cover/(?P<msgid>.+)/mbox/$',
        cover_views.cover_mbox,
        name='cover-mbox',
    ),
    re_path(
        r'^project/(?P<project_id>[^/]+)/cover/(?P<msgid>.+)/$',
        cover_views.cover_detail,
        name='cover-detail',
    ),
    # ... old-style /cover/N/* urls
    re_path(
        r'^cover/(?P<cover_id>\d+)/mbox/$',
        cover_views.cover_mbox_by_id,
        name='cover-mbox-redirect',
    ),
    re_path(
        r'^cover/(?P<cover_id>\d+)/$',
        cover_views.cover_by_id,
        name='cover-id-redirect',
    ),
    # comment views
    re_path(
        r'^comment/(?P<comment_id>\d+)/$',
        comment_views.comment,
        name='comment-redirect',
    ),
    # series views
    re_path(
        r'^series/(?P<series_id>\d+)/mbox/$',
        series_views.series_mbox,
        name='series-mbox',
    ),
    # logged-in user stuff
    re_path(r'^user/$', user_views.profile, name='user-profile'),
    re_path(r'^user/todo/$', user_views.todo_lists, name='user-todos'),
    re_path(
        r'^user/todo/(?P<project_id>[^/]+)/$',
        user_views.todo_list,
        name='user-todo',
    ),
    re_path(r'^user/bundles/$', bundle_views.bundle_list, name='user-bundles'),
    re_path(r'^user/link/$', user_views.link, name='user-link'),
    re_path(
        r'^user/unlink/(?P<person_id>[^/]+)/$',
        user_views.unlink,
        name='user-unlink',
    ),
    # password change
    re_path(
        r'^user/password-change/$',
        auth_views.PasswordChangeView.as_view(),
        name='password_change',
    ),
    re_path(
        r'^user/password-change/done/$',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done',
    ),
    re_path(
        r'^user/password-reset/$',
        auth_views.PasswordResetView.as_view(),
        name='password_reset',
    ),
    re_path(
        r'^user/password-reset/mail-sent/$',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    re_path(
        r'^user/password-reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    re_path(
        r'^user/password-reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    # login/logout
    re_path(
        r'^user/login/$',
        auth_views.LoginView.as_view(template_name='patchwork/login.html'),
        name='auth_login',
    ),
    re_path(
        r'^user/logout/$',
        auth_views.LogoutView.as_view(next_page=reverse_lazy('project-list')),
        name='auth_logout',
    ),
    # registration
    re_path(r'^register/', user_views.register, name='user-register'),
    # public view for bundles
    re_path(
        r'^bundle/(?P<username>[^/]*)/(?P<bundlename>[^/]*)/$',
        bundle_views.bundle_detail,
        name='bundle-detail',
    ),
    re_path(
        r'^bundle/(?P<username>[^/]*)/(?P<bundlename>[^/]*)/mbox/$',
        bundle_views.bundle_mbox,
        name='bundle-mbox',
    ),
    re_path(
        r'^confirm/(?P<key>[0-9a-f]+)/$',
        notification_views.confirm,
        name='confirm',
    ),
    # submitter autocomplete
    re_path(r'^submitter/$', api_views.submitters, name='api-submitters'),
    re_path(r'^delegate/$', api_views.delegates, name='api-delegates'),
    # email setup
    re_path(r'^mail/$', mail_views.settings, name='mail-settings'),
    re_path(r'^mail/optout/$', mail_views.optout, name='mail-optout'),
    re_path(r'^mail/optin/$', mail_views.optin, name='mail-optin'),
    # about
    re_path(r'^about/$', about_views.about, name='about'),
    # legacy redirects
    re_path(r'^help/$', about_views.redirect, name='help'),
    re_path(r'^help/about/$', about_views.redirect, name='help-about'),
]

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar  # noqa

    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]

if settings.ENABLE_XMLRPC:
    urlpatterns += [
        re_path(r'xmlrpc/$', xmlrpc_views.xmlrpc, name='xmlrpc'),
        re_path(
            r'^project/(?P<project_id>[^/]+)/pwclientrc/$',
            pwclient_views.pwclientrc,
            name='pwclientrc',
        ),
        # legacy redirect
        re_path(
            r'^help/pwclient/$', about_views.redirect, name='help-pwclient'
        ),
    ]

if settings.ENABLE_REST_API:
    if 'rest_framework' not in settings.INSTALLED_APPS:
        raise RuntimeError(
            'djangorestframework must be installed to enable the REST API.'
        )

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
        re_path(r'^$', api_index_views.IndexView.as_view(), name='api-index'),
        re_path(
            r'^users/$',
            api_user_views.UserList.as_view(),
            name='api-user-list',
        ),
        re_path(
            r'^users/(?P<pk>[^/]+)/$',
            api_user_views.UserDetail.as_view(),
            name='api-user-detail',
        ),
        re_path(
            r'^people/$',
            api_person_views.PersonList.as_view(),
            name='api-person-list',
        ),
        re_path(
            r'^people/(?P<pk>[^/]+)/$',
            api_person_views.PersonDetail.as_view(),
            name='api-person-detail',
        ),
        re_path(
            r'^covers/$',
            api_cover_views.CoverList.as_view(),
            name='api-cover-list',
        ),
        re_path(
            r'^covers/(?P<pk>[^/]+)/$',
            api_cover_views.CoverDetail.as_view(),
            name='api-cover-detail',
        ),
        re_path(
            r'^patches/$',
            api_patch_views.PatchList.as_view(),
            name='api-patch-list',
        ),
        re_path(
            r'^patches/(?P<pk>[^/]+)/$',
            api_patch_views.PatchDetail.as_view(),
            name='api-patch-detail',
        ),
        re_path(
            r'^patches/(?P<patch_id>[^/]+)/checks/$',
            api_check_views.CheckListCreate.as_view(),
            name='api-check-list',
        ),
        re_path(
            r'^patches/(?P<patch_id>[^/]+)/checks/(?P<check_id>[^/]+)/$',
            api_check_views.CheckDetail.as_view(),
            name='api-check-detail',
        ),
        re_path(
            r'^series/$',
            api_series_views.SeriesList.as_view(),
            name='api-series-list',
        ),
        re_path(
            r'^series/(?P<pk>[^/]+)/$',
            api_series_views.SeriesDetail.as_view(),
            name='api-series-detail',
        ),
        re_path(
            r'^bundles/$',
            api_bundle_views.BundleList.as_view(),
            name='api-bundle-list',
        ),
        re_path(
            r'^bundles/(?P<pk>[^/]+)/$',
            api_bundle_views.BundleDetail.as_view(),
            name='api-bundle-detail',
        ),
        re_path(
            r'^projects/$',
            api_project_views.ProjectList.as_view(),
            name='api-project-list',
        ),
        re_path(
            r'^projects/(?P<pk>[^/]+)/$',
            api_project_views.ProjectDetail.as_view(),
            name='api-project-detail',
        ),
        re_path(
            r'^events/$',
            api_event_views.EventList.as_view(),
            name='api-event-list',
        ),
    ]

    api_1_1_patterns = [
        re_path(
            r'^patches/(?P<pk>[^/]+)/comments/$',
            api_comment_views.PatchCommentList.as_view(),
            name='api-patch-comment-list',
        ),
        re_path(
            r'^covers/(?P<pk>[^/]+)/comments/$',
            api_comment_views.CoverCommentList.as_view(),
            name='api-cover-comment-list',
        ),
    ]

    urlpatterns += [
        re_path(
            r'^api/(?:(?P<version>(1.0|1.1|1.2))/)?', include(api_patterns)
        ),
        re_path(
            r'^api/(?:(?P<version>(1.1|1.2))/)?', include(api_1_1_patterns)
        ),
        # token change
        re_path(
            r'^user/generate-token/$',
            user_views.generate_token,
            name='generate_token',
        ),
    ]


# redirect from old urls
if settings.COMPAT_REDIR:
    urlpatterns += [
        re_path(
            r'^user/bundle/(?P<bundle_id>[^/]+)/$',
            bundle_views.bundle_detail_redir,
            name='bundle-redir',
        ),
        re_path(
            r'^user/bundle/(?P<bundle_id>[^/]+)/mbox/$',
            bundle_views.bundle_mbox_redir,
            name='bundle-mbox-redir',
        ),
    ]
