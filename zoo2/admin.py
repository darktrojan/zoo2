from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from zoo2.models import *


class ViewOnSiteMixin(object):
	def view_on_site2(self, obj):
		return mark_safe('<a href="%s" class="viewsitelink2">View on site</a>' % obj.get_absolute_url())
	view_on_site2.allow_tags = True
	view_on_site2.short_description = 'View on site'


class LocaleAdmin(admin.ModelAdmin):
	list_display = ('code', 'name')
	ordering = ('code',)


class RepoAdmin(ViewOnSiteMixin, admin.ModelAdmin):
	list_display = ('full_name', 'addon_name', 'owner', 'view_on_site2')


class TranslationAdmin(ViewOnSiteMixin, admin.ModelAdmin):
	list_display = ('repo', 'locale', 'owner', 'view_on_site2')


class FileAdmin(admin.ModelAdmin):
	list_display = ('repo', 'path', 'string_count')


class StringAdmin(admin.ModelAdmin):
	list_display = ('file', 'locale', 'key', 'value')
	list_display_links = ('key',)
	list_filter = ('file', 'locale')


class UserProfileInline(admin.StackedInline):
	model = UserProfile
	can_delete = False


class UserAdmin(UserAdmin):
	inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Locale, LocaleAdmin)
admin.site.register(Repo, RepoAdmin)
admin.site.register(Translation, TranslationAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(String, StringAdmin)
admin.site.register(HTMLBlock)
