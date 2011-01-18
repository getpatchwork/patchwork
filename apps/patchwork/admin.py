from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from patchwork.models import Project, Person, UserProfile, State, Patch, \
         Comment, Bundle

admin_site = admin.AdminSite()

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'linkname','listid', 'listemail')
admin_site.register(Project, ProjectAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'has_account')
    search_fields = ('name', 'email')
    def has_account(self, person):
        return bool(person.user)
    has_account.boolean = True
    has_account.admin_order_field = 'user'
    has_account.short_description = 'Account'
admin_site.register(Person, PersonAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
admin_site.register(UserProfile, UserProfileAdmin)

class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_required')
admin_site.register(State, StateAdmin)

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
admin_site.register(Patch, PatchAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('patch', 'submitter', 'date')
    search_fields = ('patch__name', 'submitter__name', 'submitter__email')
    date_hierarchy = 'date'
admin_site.register(Comment, CommentAdmin)

class BundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'project', 'public')
    list_filter = ('public', 'project')
    search_fields = ('name', 'owner')
admin_site.register(Bundle, BundleAdmin)

admin_site.register(User, UserAdmin)

class SiteAdmin(admin.ModelAdmin):
    pass
admin_site.register(Site, SiteAdmin)

