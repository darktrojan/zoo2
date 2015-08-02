from __future__ import absolute_import

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoo2.settings')

from celery import Celery
from django.conf import settings
from django.contrib.auth.models import User

from github import api, raw
from mozilla import chrome_manifest
from zoo2.models import *

app = Celery('zoo2', broker='django://')
app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task
def create_repo(full_name, branch, owner_pk):
	# assume it doesn't exist already TODO
	owner = User.objects.get(pk=owner_pk)
	repo = Repo(full_name=full_name, branch=branch, owner=owner)

	head_commit = api.get_head_commit_sha(full_name, branch)
	manifest = raw.get_raw_file(full_name, head_commit, 'chrome.manifest')

	locale_path, existing = chrome_manifest.parse(manifest)
	repo.locale_path = locale_path
	repo.translations_list_set = existing
	repo.head_commit = head_commit
	repo.save()

	repo.find_files()

	# TODO fork the repo
	api.update_head_commit_sha(repo.fork_name, 'zoo2', head_commit, force=True)

	locale = Locale.objects.get(code='en-US')
	for f in repo.file_set.all():
		download_file.delay(f.pk, locale.code, head_commit)

@app.task
def download_translation(translation_pk):
	t = Translation.objects.get(pk=translation_pk)
	for f in t.repo.file_set.all():
		download_file.delay(f.pk, t.locale.code, t.repo.head_commit)

@app.task
def download_file(file_pk, locale_code, head_commit):
	f = File.objects.get(pk=file_pk)
	l = Locale.objects.get(code=locale_code)
	f.download_from_source(l, head_commit)

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
