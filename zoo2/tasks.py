from __future__ import absolute_import

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoo2.settings')

from celery import Celery
from django.conf import settings

from github import api, raw
from mozilla import chrome_manifest
from zoo2.models import *

app = Celery('zoo2', broker='django://')
app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task
def download_translation(translation_pk, use_fork=False):
	t = Translation.objects.get(pk=translation_pk)
	t.download_from_source(use_fork)

@app.task
def save_translation(translation_pk):
	t = Translation.objects.get(pk=translation_pk)
	print 'Saving to GitHub'
	t.save_to_github()
	print 'Creating pull request'
	original = t.pull_request
	t.create_pull_request()
	if t.pull_request == original:
		print 'Already had a pull request'
	else:
		print 'New pull request: %d' % t.pull_request

@app.task
def create_repo(full_name, branch):
	# assume it doesn't exist already
	repo = Repo(full_name=full_name, branch=branch)

	head_commit = api.get_head_commit_sha(full_name, branch)
	manifest = raw.get_raw_file(full_name, head_commit, 'chrome.manifest')

	locale_path, existing = chrome_manifest.parse(manifest)
	repo.locale_path = locale_path
	repo.head_commit = head_commit
	repo.save()

	repo.find_files()

	api.update_head_commit_sha(repo.fork_name, 'zoo2', head_commit, force=True)

	for l in existing:
		try:
			locale = Locale.objects.get(code=l)
			translation = Translation(repo=repo, locale=locale, head_commit=head_commit)
			translation.save()

			download_translation.delay(translation.pk)
		except Locale.DoesNotExist:
			pass
