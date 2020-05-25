# Patchwork - automated patch tracking system
# Copyright (C) 2008 Jeremy Kerr <jk@ozlabs.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Prefetch

from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Cover
from patchwork.models import CoverComment
from patchwork.models import DelegationRule
from patchwork.models import Patch
from patchwork.models import PatchComment
from patchwork.models import PatchRelation
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import SeriesReference
from patchwork.models import State
from patchwork.models import Tag
from patchwork.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'user profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class DelegationRuleInline(admin.TabularInline):
    model = DelegationRule
    fields = ('path', 'user', 'priority')


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'linkname', 'listid', 'listemail')
    inlines = [
        DelegationRuleInline,
    ]


admin.site.register(Project, ProjectAdmin)


class PersonAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'has_account')
    search_fields = ('name', 'email')

    def has_account(self, person):
        return bool(person.user)

    has_account.boolean = True
    has_account.admin_order_field = 'user'
    has_account.short_description = 'Account'


admin.site.register(Person, PersonAdmin)


class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_required')


admin.site.register(State, StateAdmin)


class CoverAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'date')
    list_filter = ('project', )
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'


admin.site.register(Cover, CoverAdmin)


class PatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'state', 'date',
                    'archived', 'is_pull_request')
    list_filter = ('project', 'submitter', 'state', 'archived')
    list_select_related = ('submitter', 'project', 'state')
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'

    def is_pull_request(self, patch):
        return bool(patch.pull_url)

    is_pull_request.boolean = True
    is_pull_request.admin_order_field = 'pull_url'
    is_pull_request.short_description = 'Pull'


admin.site.register(Patch, PatchAdmin)


class CoverCommentAdmin(admin.ModelAdmin):
    list_display = ('cover', 'submitter', 'date')
    search_fields = ('cover__name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'


admin.site.register(CoverComment, CoverCommentAdmin)


class PatchCommentAdmin(admin.ModelAdmin):
    list_display = ('patch', 'submitter', 'date')
    search_fields = ('patch__name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'


admin.site.register(PatchComment, PatchCommentAdmin)


class PatchInline(admin.StackedInline):
    model = Patch
    extra = 0


class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'date', 'version', 'total',
                    'received_total', 'received_all')
    list_filter = ('project', 'submitter')
    list_select_related = ('submitter', 'project')
    readonly_fields = ('received_total', 'received_all')
    search_fields = ('submitter__name', 'submitter__email')
    exclude = ('patches', )
    inlines = (PatchInline, )

    def received_all(self, series):
        return series.received_all
    received_all.boolean = True

    def get_queryset(self, request):
        qs = super(SeriesAdmin, self).get_queryset(request)
        return qs.prefetch_related(Prefetch(
            'patches', Patch.objects.only('series',)))


admin.site.register(Series, SeriesAdmin)


class SeriesReferenceAdmin(admin.ModelAdmin):
    model = SeriesReference


admin.site.register(SeriesReference, SeriesReferenceAdmin)


class CheckAdmin(admin.ModelAdmin):
    list_display = ('patch', 'user', 'state', 'target_url',
                    'description', 'context')
    exclude = ('date', )
    search_fields = ('patch__name', 'project__name')
    date_hierarchy = 'date'


admin.site.register(Check, CheckAdmin)


class BundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'project', 'public')
    list_filter = ('public', 'project')
    search_fields = ('name', 'owner')


admin.site.register(Bundle, BundleAdmin)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


admin.site.register(Tag, TagAdmin)


class PatchRelationAdmin(admin.ModelAdmin):
    model = PatchRelation


admin.site.register(PatchRelation, PatchRelationAdmin)
