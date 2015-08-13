from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from zoo2.models import *


class UserProfileInline(admin.StackedInline):
	model = UserProfile
	can_delete = False


class UserAdmin(UserAdmin):
	inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Locale)
admin.site.register(Repo)
admin.site.register(Translation)
admin.site.register(File)
admin.site.register(String)
admin.site.register(HTMLBlock)
