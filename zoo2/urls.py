from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

translation_patterns = [
	url(r'^$', 'zoo2.views.translation', name='translation'),
	url(r'^/push$', 'zoo2.views.push', name='push'),
	url(r'^/edit/(?P<path>.*)$', 'zoo2.views.edit', name='edit'),
	url(r'^/save/(?P<path>.*)$', 'zoo2.views.save', name='save'),
]

repo_patterns = [
	url(r'^$', 'zoo2.views.repo', name='repo'),
	url(r'^/new$', 'zoo2.views.new', name='new'),
	url(r'^/(?P<code>[a-z]{2,3}(-[A-Z]{2})?)', include(translation_patterns)),
]

urlpatterns = patterns('',
	url(r'^$', 'zoo2.views.index', name='index'),
	url(r'^(?P<full_name>\w+/\w+)', include(repo_patterns)),
	url(r'^hook$', 'zoo2.views.hook'),
	url(r'^github_auth$', 'zoo2.views.github_auth'),
	url(r'^admin/', include(admin.site.urls)),
)
