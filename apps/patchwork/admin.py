from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from patchwork.models import Project, Person, UserProfile, State, Patch, \
         Comment, Bundle

admin_site = admin.AdminSite()

class ProjectAdmin(admin.ModelAdmin):
    pass
admin_site.register(Project, ProjectAdmin)

class PersonAdmin(admin.ModelAdmin):
    pass
admin_site.register(Person, PersonAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    pass
admin_site.register(UserProfile, UserProfileAdmin)

class StateAdmin(admin.ModelAdmin):
    pass
admin_site.register(State, StateAdmin)

class PatchAdmin(admin.ModelAdmin):
    pass
admin_site.register(Patch, PatchAdmin)

class CommentAdmin(admin.ModelAdmin):
    pass
admin_site.register(Comment, CommentAdmin)

class BundleAdmin(admin.ModelAdmin):
    pass
admin_site.register(Bundle, BundleAdmin)

admin_site.register(User, UserAdmin)

class SiteAdmin(admin.ModelAdmin):
    pass
admin_site.register(Site, SiteAdmin)

