from __future__ import absolute_import

import os
import re
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoo2.settings')

from celery import Celery, group
from django.contrib.auth.models import User
from django.db.models import F

from github import api, raw
from mozilla.chrome_manifest import ChromeManifestParser
from mozilla.install_rdf import InstallRDFParser
from zoo2.models import *

app = Celery('zoo2', broker='django://')
app.config_from_object('django.conf:settings')


@app.task
def create_repo(full_name, branch, owner_pk):
	# assume it doesn't exist already TODO
	owner = User.objects.get(pk=owner_pk)
	repo = Repo(full_name=full_name, branch=branch, owner=owner)

	head_commit = api.get_head_commit_sha(full_name, branch)
	manifest = raw.get_raw_file(full_name, head_commit, 'chrome.manifest')

	parser = ChromeManifestParser(manifest)
	repo.locale_path = parser.locale_path
	repo.translations_list_set = parser.existing
	repo.head_commit = head_commit
	repo.save()

	for f in repo.find_files(head_commit):
		File(repo=repo, path=f).save()

	if not api.create_fork(repo.full_name):
		# returns True if a fork was created, and that takes time so we can't update now
		api.update_head_commit_sha(repo.fork_name, 'zoo2', head_commit, force=True)

	token = owner.profile.github_token
	api.add_webhook(repo.full_name, token)

	download_readme.delay(repo.pk, head_commit)

	for f in repo.file_set.all():
		if f.path == 'install.rdf':
			download_install_rdf.delay(repo.pk, head_commit)
			continue

		download_file.delay(f.pk, 'en-US', head_commit)


@app.task
def update_repo_from_upstream(repo_pk, head_commit, commits_data):
	repo = Repo.objects.get(pk=repo_pk)
	# wait a bit to give GitHub a chance to catch itself up
	update_fork.apply_async(args=[repo_pk, head_commit], countdown=3)

	# TODO update translations' head_commit if ...?
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
	print 'These files have changed: %s' % ', '.join(changed_files)

	if 'install.rdf' in changed_files:
		download_install_rdf.delay(repo.pk, head_commit)

	if 'chrome.manifest' in changed_files:
		manifest = raw.get_raw_file(repo.full_name, head_commit, 'chrome.manifest')

		parser = ChromeManifestParser(manifest)
		repo.translations_list_set = parser.existing
		repo.save(update_fields=['translations_list'])

	if 'zoo.md' in changed_files:
		download_readme.delay(repo.pk, head_commit)

	if file_list_changed:
		existing_files = [f.path for f in repo.file_set.all()]

		for f in repo.find_files(head_commit):
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
				if code != 'en-US':
					# make sure we have a translation, otherwise don't bother
					locale = Locale.objects.get(code=code)
					repo.translation_set.get(locale=locale)
				path = match.group(3)
				file = repo.file_set.get(path=path)
				download_file.delay(file.pk, code, head_commit)
			except Locale.DoesNotExist:
				pass
			except Translation.DoesNotExist:
				pass
			except File.DoesNotExist:
				pass


@app.task
def update_fork(repo_pk, head_commit):
	repo = Repo.objects.get(pk=repo_pk)
	repo.update_fork(head_commit)


@app.task
def download_translation(translation_pk):
	t = Translation.objects.get(pk=translation_pk)
	signatures = []
	for f in t.repo.file_set.all():
		if f.path == 'install.rdf':
			continue

		signatures.append(
			download_file.s(f.pk, t.locale.code, t.repo.head_commit, mark_translation=translation_pk)
		)

	t.busy = len(signatures)
	t.save(update_fields=['busy'])
	group(signatures).delay()


@app.task
def download_install_rdf(repo_pk, head_commit):
	repo = Repo.objects.get(pk=repo_pk)
	try:
		file = repo.file_set.get(path='install.rdf')
	except File.DoesNotExist:
		file = File(repo=repo, path='install.rdf')
		file.save()

	f = raw.get_raw_file(repo.full_name, head_commit, 'install.rdf')
	parser = InstallRDFParser(f)
	repo.addon_name = parser.translations['en-US']['name']
	repo.save(update_fields=['addon_name'])
	for l, t in parser.translations.iteritems():
		try:
			locale = Locale.objects.get(code=l)
			for k in ['name', 'description']:
				try:
					string = file.string_set.get(locale=locale, key=k)
				except String.DoesNotExist:
					string = String(file=file, locale=locale, key=k)
				string.value = t[k]
				string.save()
		except Locale.DoesNotExist:
			pass


@app.task
def download_readme(repo_pk, head_commit):
	repo = Repo.objects.get(pk=repo_pk)
	file = raw.get_raw_file(repo.full_name, head_commit, 'zoo.md')
	repo.readme = file if file is not None else ''
	repo.save(update_fields=['readme'])


@app.task
def download_file(file_pk, locale_code, head_commit, mark_translation=None):
	f = File.objects.get(pk=file_pk)
	l = Locale.objects.get(code=locale_code)
	f.download_from_source(l, head_commit)

	if mark_translation is not None:
		Translation.objects.filter(pk=mark_translation).update(busy=F('busy') - 1)


@app.task
def save_translation(translation_pk):
	t = Translation.objects.get(pk=translation_pk)
	t.save_to_github()
	original = t.pull_request
	t.create_pull_request()
	if t.pull_request == original:
		print 'Already had a pull request: %d' % t.pull_request
	else:
		print 'New pull request: %d' % t.pull_request
