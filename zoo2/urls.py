from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^(?P<full_name>\w+/\w+)$', 'zoo2.views.repo', name='repo'),
	url(r'^(?P<full_name>\w+/\w+)/(?P<code>[a-z]{2,3}(-[A-Z]{2})?)$', 'zoo2.views.locale', name='locale'),
	url(r'^(?P<full_name>\w+/\w+)/(?P<code>[a-z]{2,3}(-[A-Z]{2})?)/edit/(?P<path>.*)$', 'zoo2.views.file', name='file'),
	url(r'^(?P<full_name>\w+/\w+)/(?P<code>[a-z]{2,3}(-[A-Z]{2})?)/save/(?P<path>.*)$', 'zoo2.views.save', name='save'),
	url(r'^hook$', 'zoo2.views.hook'),
	url(r'^admin/', include(admin.site.urls)),
)
