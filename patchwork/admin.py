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

from __future__ import absolute_import

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from patchwork.models import Bundle
from patchwork.models import Check
from patchwork.models import Comment
from patchwork.models import CoverLetter
from patchwork.models import DelegationRule
from patchwork.models import Patch
from patchwork.models import Person
from patchwork.models import Project
from patchwork.models import Series
from patchwork.models import SeriesReference
from patchwork.models import State
from patchwork.models import Submission
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


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'date')
    list_filter = ('project', )
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'


admin.site.register(Submission, SubmissionAdmin)
admin.site.register(CoverLetter, SubmissionAdmin)


class PatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitter', 'project', 'state', 'date',
                    'archived', 'is_pull_request')
    list_filter = ('project', 'state', 'archived')
    search_fields = ('name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'

    def is_pull_request(self, patch):
        return bool(patch.pull_url)

    is_pull_request.boolean = True
    is_pull_request.admin_order_field = 'pull_url'
    is_pull_request.short_description = 'Pull'


admin.site.register(Patch, PatchAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('submission', 'submitter', 'date')
    search_fields = ('submission__name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'


admin.site.register(Comment, CommentAdmin)


class PatchInline(admin.StackedInline):
    model = Series.patches.through
    extra = 0


class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'submitter', 'version', 'total',
                    'received_total', 'received_all')
    readonly_fields = ('received_total', 'received_all')
    search_fields = ('submitter_name', 'submitter_email')
    exclude = ('patches', )
    inlines = (PatchInline, )

    def received_all(self, series):
        return series.received_all
    received_all.boolean = True


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
