from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

translation_patterns = [
	url(r'^$', 'zoo2.views.translation', name='translation'),
	url(r'^/push$', 'zoo2.views.push', name='push'),
	url(r'^/edit/(?P<path>.*)$', 'zoo2.views.file', name='edit', kwargs=({'fileaction': 'edit'})),
	url(r'^/view/(?P<path>.*)$', 'zoo2.views.file', name='view', kwargs=({'fileaction': 'view'})),
	url(r'^/save/(?P<path>.*)$', 'zoo2.views.save', name='save'),
]

repo_patterns = [
	url(r'^$', 'zoo2.views.repo', name='repo'),
	url(r'^/new$', 'zoo2.views.new', name='new'),
	url(r'^/(?P<code>[a-z]{2,3}(-[A-Z]{2})?)', include(translation_patterns)),
]

urlpatterns = patterns(
	'',
	url(r'^$', 'zoo2.views.index', name='index'),
	url(r'^log_out$', 'zoo2.views.log_out', name='log_out'),
	url(r'^(?P<full_name>\w+/\w+)', include(repo_patterns)),
	url(r'^hook$', 'zoo2.views.hook'),
	url(r'^persona_auth$', 'zoo2.views.persona_auth', name='persona_auth'),
	url(r'^github_auth$', 'zoo2.views.github_auth', name='github_auth'),
	url(r'^profile$', 'zoo2.views.profile', name='profile'),
	url(r'^admin/', include(admin.site.urls)),
)
