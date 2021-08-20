# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.urls import reverse_lazy

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
    path('admin/', admin.site.urls),
    path('', project_views.project_list, name='project-list'),
    path(
        'project/<project_id>/list/',
        patch_views.patch_list,
        name='patch-list',
    ),
    path(
        'project/<project_id>/bundles/',
        bundle_views.bundle_list,
        name='bundle-list',
    ),
    path(
        'project/<project_id>/',
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
    path(
        'project/<project_id>/patch/<path:msgid>/raw/',
        patch_views.patch_raw,
        name='patch-raw',
    ),
    path(
        'project/<project_id>/patch/<path:msgid>/mbox/',
        patch_views.patch_mbox,
        name='patch-mbox',
    ),
    path(
        'project/<project_id>/patch/<path:msgid>/',
        patch_views.patch_detail,
        name='patch-detail',
    ),
    # ... old-style /patch/N/* urls
    path(
        'patch/<int:patch_id>/raw/',
        patch_views.patch_raw_by_id,
        name='patch-raw-redirect',
    ),
    path(
        'patch/<int:patch_id>/mbox/',
        patch_views.patch_mbox_by_id,
        name='patch-mbox-redirect',
    ),
    path(
        'patch/<int:patch_id>/',
        patch_views.patch_by_id,
        name='patch-id-redirect',
    ),
    # cover views
    path(
        'project/<project_id>/cover/<path:msgid>/mbox/',
        cover_views.cover_mbox,
        name='cover-mbox',
    ),
    path(
        'project/<project_id>/cover/<path:msgid>/',
        cover_views.cover_detail,
        name='cover-detail',
    ),
    # ... old-style /cover/N/* urls
    path(
        'cover/<int:cover_id>/mbox/',
        cover_views.cover_mbox_by_id,
        name='cover-mbox-redirect',
    ),
    path(
        'cover/<int:cover_id>/',
        cover_views.cover_by_id,
        name='cover-id-redirect',
    ),
    # comment views
    path(
        'comment/<int:comment_id>/',
        comment_views.comment,
        name='comment-redirect',
    ),
    # series views
    path(
        'series/<int:series_id>/mbox/',
        series_views.series_mbox,
        name='series-mbox',
    ),
    # logged-in user stuff
    path('user/', user_views.profile, name='user-profile'),
    path('user/todo/', user_views.todo_lists, name='user-todos'),
    path('user/todo/<project_id>/', user_views.todo_list, name='user-todo'),
    path('user/bundles/', bundle_views.bundle_list, name='user-bundles'),
    path('user/link/', user_views.link, name='user-link'),
    path('user/unlink/<person_id>/', user_views.unlink, name='user-unlink'),
    # password change
    path(
        'user/password-change/',
        auth_views.PasswordChangeView.as_view(),
        name='password_change',
    ),
    path(
        'user/password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done',
    ),
    path(
        'user/password-reset/',
        auth_views.PasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'user/password-reset/mail-sent/',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'user/password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'user/password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),
    # login/logout
    path(
        'user/login/',
        auth_views.LoginView.as_view(template_name='patchwork/login.html'),
        name='auth_login',
    ),
    path(
        'user/logout/',
        auth_views.LogoutView.as_view(next_page=reverse_lazy('project-list')),
        name='auth_logout',
    ),
    # registration
    path('register/', user_views.register, name='user-register'),
    # public view for bundles
    path(
        'bundle/<username>/<bundlename>/',
        bundle_views.bundle_detail,
        name='bundle-detail',
    ),
    path(
        'bundle/<username>/<bundlename>/mbox/',
        bundle_views.bundle_mbox,
        name='bundle-mbox',
    ),
    re_path(
        r'^confirm/(?P<key>[0-9a-f]+)/$',
        notification_views.confirm,
        name='confirm',
    ),
    # submitter autocomplete
    path('submitter/', api_views.submitters, name='api-submitters'),
    path('delegate/', api_views.delegates, name='api-delegates'),
    # email setup
    path('mail/', mail_views.settings, name='mail-settings'),
    path('mail/optout/', mail_views.optout, name='mail-optout'),
    path('mail/optin/', mail_views.optin, name='mail-optin'),
    # about
    path('about/', about_views.about, name='about'),
    # legacy redirects
    path('help/', about_views.redirect, name='help'),
    path('help/about/', about_views.redirect, name='help-about'),
]

if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar  # noqa

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

if settings.ENABLE_XMLRPC:
    urlpatterns += [
        path('xmlrpc/', xmlrpc_views.xmlrpc, name='xmlrpc'),
        path(
            'project/<project_id>/pwclientrc/',
            pwclient_views.pwclientrc,
            name='pwclientrc',
        ),
        # legacy redirect
        path('help/pwclient/', about_views.redirect, name='help-pwclient'),
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
        path('', api_index_views.IndexView.as_view(), name='api-index'),
        path(
            'users/',
            api_user_views.UserList.as_view(),
            name='api-user-list',
        ),
        path(
            'users/<int:pk>/',
            api_user_views.UserDetail.as_view(),
            name='api-user-detail',
        ),
        path(
            'people/',
            api_person_views.PersonList.as_view(),
            name='api-person-list',
        ),
        path(
            'people/<int:pk>/',
            api_person_views.PersonDetail.as_view(),
            name='api-person-detail',
        ),
        path(
            'covers/',
            api_cover_views.CoverList.as_view(),
            name='api-cover-list',
        ),
        path(
            'covers/<int:pk>/',
            api_cover_views.CoverDetail.as_view(),
            name='api-cover-detail',
        ),
        path(
            'patches/',
            api_patch_views.PatchList.as_view(),
            name='api-patch-list',
        ),
        path(
            'patches/<int:pk>/',
            api_patch_views.PatchDetail.as_view(),
            name='api-patch-detail',
        ),
        path(
            'patches/<int:patch_id>/checks/',
            api_check_views.CheckListCreate.as_view(),
            name='api-check-list',
        ),
        path(
            'patches/<int:patch_id>/checks/<int:check_id>/',
            api_check_views.CheckDetail.as_view(),
            name='api-check-detail',
        ),
        path(
            'series/',
            api_series_views.SeriesList.as_view(),
            name='api-series-list',
        ),
        path(
            'series/<int:pk>/',
            api_series_views.SeriesDetail.as_view(),
            name='api-series-detail',
        ),
        path(
            'bundles/',
            api_bundle_views.BundleList.as_view(),
            name='api-bundle-list',
        ),
        path(
            'bundles/<int:pk>/',
            api_bundle_views.BundleDetail.as_view(),
            name='api-bundle-detail',
        ),
        path(
            'projects/',
            api_project_views.ProjectList.as_view(),
            name='api-project-list',
        ),
        path(
            'projects/<pk>/',
            api_project_views.ProjectDetail.as_view(),
            name='api-project-detail',
        ),
        path(
            'events/',
            api_event_views.EventList.as_view(),
            name='api-event-list',
        ),
    ]

    api_1_1_patterns = [
        path(
            'patches/<int:patch_id>/comments/',
            api_comment_views.PatchCommentList.as_view(),
            name='api-patch-comment-list',
        ),
        path(
            'covers/<int:cover_id>/comments/',
            api_comment_views.CoverCommentList.as_view(),
            name='api-cover-comment-list',
        ),
    ]

    api_1_3_patterns = [
        path(
            'patches/<int:patch_id>/comments/<int:comment_id>/',
            api_comment_views.PatchCommentDetail.as_view(),
            name='api-patch-comment-detail',
        ),
        path(
            'covers/<int:cover_id>/comments/<int:comment_id>/',
            api_comment_views.CoverCommentDetail.as_view(),
            name='api-cover-comment-detail',
        ),
    ]

    urlpatterns += [
        re_path(
            r'^api/(?:(?P<version>(1.0|1.1|1.2|1.3))/)?', include(api_patterns)
        ),
        re_path(
            r'^api/(?:(?P<version>(1.1|1.2|1.3))/)?', include(api_1_1_patterns)
        ),
        re_path(
            r'^api/(?:(?P<version>(1.3))/)?', include(api_1_3_patterns)
        ),
        # token change
        path(
            'user/generate-token/',
            user_views.generate_token,
            name='generate_token',
        ),
    ]


# redirect from old urls
if settings.COMPAT_REDIR:
    urlpatterns += [
        path(
            'user/bundle/<bundle_id>/',
            bundle_views.bundle_detail_redir,
            name='bundle-redir',
        ),
        path(
            'user/bundle/<bundle_id>/mbox/',
            bundle_views.bundle_mbox_redir,
            name='bundle-mbox-redir',
        ),
    ]
