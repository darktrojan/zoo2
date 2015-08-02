from __future__ import absolute_import

import os, re
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

	for f in repo.find_files():
		File(repo=repo, path=f).save()

	if not api.create_fork(repo.full_name):
		# returns True if a fork was created, and that takes time so we can't update now
		api.update_head_commit_sha(repo.fork_name, 'zoo2', head_commit, force=True)

	for f in repo.file_set.all():
		download_file.delay(f.pk, 'en-US', head_commit)

@app.task
def update_repo_from_upstream(repo_pk, head_commit, commits_data):
	repo = Repo.objects.get(pk=repo_pk)
	repo.update_fork(head_commit)

	# TODO stop assuming that locale_path hasn't changed
	m = os.path.join(repo.locale_path, '([a-z]{2,3}(-[A-Z]{2})?)', '(.*)$')

	# TODO if this is a forced update, there are no commits
	changed_files = []
	file_list_changed = False
	for c in commits_data:
		for t in ['added', 'removed']:
			for f in c[t]:
				changed_files.append(f)
				match = re.match(m, f)
				if match is not None and match.group(1) == 'en-US':
					file_list_changed = True
		for f in c['modified']:
			changed_files.append(f)

	changed_files = frozenset(changed_files)
	print 'These files have changed:'
	print changed_files

	if 'chrome.manifest' in changed_files:
		manifest = raw.get_raw_file(repo.full_name, head_commit, 'chrome.manifest')

		locale_path, existing = chrome_manifest.parse(manifest)
		repo.translations_list_set = existing
		repo.save(update_fields=['translations_list'])

	if file_list_changed:
		existing_files = [f.path for f in repo.file_set.all()]

		for f in repo.find_files():
			if f in existing_files:
				existing_files.remove(f)
			else:
				File(repo=repo, path=f).save()

		for f in existing_files:
			repo.file_set.get(path=f).delete()

	for f in changed_files:
		match = re.match(m, f)
		if match is not None:
			code = match.group(1)
			try:
				locale = Locale.objects.get(code=code)
				path = match.group(3)
				file = File.objects.get(repo=repo, path=path)
				download_file.delay(file.pk, code, head_commit)
			except Locale.DoesNotExist:
				pass
			except File.DoesNotExist:
				pass

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
