from __future__ import absolute_import

import os.path
from xml.sax.saxutils import escape

from django.contrib.auth.models import User
from django.db import models

from github import api, raw
from mozilla.chrome_manifest import ChromeManifestParser
from mozilla.install_rdf import InstallRDFParser
from mozilla.parser import getParser


class UserProfile(models.Model):
	user = models.OneToOneField(User, related_name='profile')
	github_username = models.CharField(max_length=255)
	github_token = models.CharField(max_length=40)


class Locale(models.Model):
	code = models.CharField(max_length=5, primary_key=True)
	name = models.CharField(max_length=32)

	def __unicode__(self):
		return '%s [%s]' % (self.name, self.code)


class Repo(models.Model):
	full_name = models.CharField(max_length=255, unique=True)
	addon_name = models.CharField(max_length=255)
	locale_path = models.CharField(max_length=255)
	translations_list = models.CharField(max_length=255, blank=True)
	branch = models.CharField(max_length=255)
	head_commit = models.CharField(max_length=40)
	owner = models.ForeignKey(User)
	amo_stub = models.CharField(max_length=32, blank=True, verbose_name='AMO stub')
	readme = models.TextField(blank=True, verbose_name='ReadMe Markdown')

	def __unicode__(self):
		return self.full_name

	def _get_fork_name(self):
		return os.path.join('darktrojan-test', self.full_name.split('/', 2)[1])
	fork_name = property(_get_fork_name)

	def _get_translations_list_set(self):
		return self.translations_list.split()

	def _set_translations_list_set(self, values):
		self.translations_list = ' '.join(values)
	translations_list_set = property(_get_translations_list_set, _set_translations_list_set)

	def find_files(self, head_commit):
		tree_sha = api.get_commit_tree_sha(self.full_name, head_commit)
		tree_sha = api.traverse_tree(
			self.full_name, os.path.join(self.locale_path, 'en-US').split('/'), tree_sha
		)
		files = api.get_tree_blobs(self.full_name, tree_sha)
		files.append('install.rdf')
		return files

	def update_fork(self, new_head_commit):
		api.update_head_commit_sha(self.fork_name, 'zoo2', new_head_commit, force=True)
		self.head_commit = new_head_commit
		self.save(update_fields=['head_commit'])


class Translation(models.Model):
	repo = models.ForeignKey(Repo)
	locale = models.ForeignKey(Locale)
	head_commit = models.CharField(max_length=40, blank=True)
	pull_request = models.IntegerField(default=0)
	dirty = models.BooleanField(default=False)
	busy = models.IntegerField(default=0)
	owner = models.ForeignKey(User)

	def __unicode__(self):
		return '%s [%s]' % (self.repo.full_name, self.branch_name)

	def _get_branch_name(self):
		return 'zoo2_%s' % self.locale.code
	branch_name = property(_get_branch_name)

	def is_owner(self, user):
		if user is None:
			return False
		return self.owner == user or self.repo.owner == user

	def save_to_github(self):
		if self.head_commit == '':
			parent_commit = self.repo.head_commit
		else:
			parent_commit = self.head_commit

		files = dict()
		for f in self.repo.file_set.all():
			# TODO stop assuming install.rdf is at the top level
			if f.path == 'install.rdf':
				name = f.string_set.get(locale=self.locale, key='name').value
				description = f.string_set.get(locale=self.locale, key='description').value
				rdf = raw.get_raw_file(self.repo.full_name, parent_commit, 'install.rdf')
				parser = InstallRDFParser(rdf)
				parser.add_locale(self.locale.code, name, description)
				files['install.rdf'] = parser.reconstruct()
				continue

			path = f.get_full_path(self.locale)
			content = f.reconstruct(self.locale)
			files[path] = content

		if self.locale.code not in self.repo.translations_list_set:
			translations_list_set = self.repo.translations_list_set
			translations_list_set.append(self.locale.code)
			self.repo.translations_list_set = translations_list_set
			self.repo.save(update_fields=['translations_list'])
			# TODO stop assuming chrome.manifest is at the top level
			manifest = raw.get_raw_file(self.repo.full_name, parent_commit, 'chrome.manifest')
			parser = ChromeManifestParser(manifest)
			parser.add_locale(self.locale.code)
			files['chrome.manifest'] = parser.reconstruct()

		tree_sha = api.get_commit_tree_sha(self.repo.fork_name, parent_commit)
		tree_sha = api.save_files(self.repo.fork_name, tree_sha, files)
		message = 'Update %s translation' % self.locale.name
		author = {
			'name': self.owner.username,
			'email': self.owner.email
		}
		self.head_commit = api.create_commit(
			self.repo.fork_name, message, tree_sha, parent_commit, author=author
		)

		api.update_head_commit_sha(self.repo.fork_name, self.branch_name, self.head_commit, force=True)

		self.dirty = False
		self.save(update_fields=['head_commit', 'dirty'])
		self.set_strings_clean()

	def create_pull_request(self):
		if self.pull_request > 0:
			pr = api.get_pull_request(self.repo.full_name, self.pull_request)
			if pr is not None and pr['state'] == 'open':
				return

		head = 'darktrojan-test:%s' % self.branch_name
		title = 'Update %s translation' % self.locale.name

		token = None
		try:
			token = self.owner.profile.github_token
		except UserProfile.DoesNotExist:
			pass

		self.pull_request = api.create_pull_request(
			self.repo.full_name, head, self.repo.branch, title, token=token
		)
		self.save(update_fields=['pull_request'])

	def set_strings_clean(self):
		for f in self.repo.file_set.all():
			for s in f.string_set.filter(locale=self.locale):
				s.dirty = False
				s.save(update_fields=['dirty'])

	def get_complete_counts(self):
		translated = 0
		duplicate = 0
		missing = 0
		total = 0
		for f in self.repo.file_set.all():
			counts = f.get_complete_counts(self.locale)
			translated += counts[0]
			duplicate += counts[1]
			missing += counts[2]
			total += counts[3]

		return translated, duplicate, missing, total

	class Meta:
		unique_together = ('repo', 'locale')


class File(models.Model):
	repo = models.ForeignKey('Repo')
	path = models.CharField(max_length=255)

	def __unicode__(self):
		return '%s %s' % (self.repo.full_name, self.path)

	def get_base_string_set(self):
		return self.string_set.filter(locale='en-US').order_by('pk')
	base_string_set = property(get_base_string_set)

	def get_string_count(self):
		return self.base_string_set.count()
	string_count = property(get_string_count)

	def get_full_path(self, locale):
		return os.path.join(self.repo.locale_path, locale.code, self.path)

	def get_complete_counts(self, locale):
		translated = 0
		duplicate = 0
		missing = 0
		for s in self.base_string_set.all():
			try:
				t = self.string_set.get(locale=locale, key=s.key)
				if t.value == s.value:
					duplicate += 1
				else:
					translated += 1
			except String.DoesNotExist:
				missing += 1

		return translated, duplicate, missing, self.base_string_set.count()

	def has_dirty_strings(self, locale):
		return self.string_set.filter(locale=locale, dirty=True).count() > 0

	def download_from_source(self, locale, head_commit):
		f = raw.get_raw_file(self.repo.full_name, head_commit, self.get_full_path(locale))

		if f is None:
			return

		if locale.code == 'en-US':
			self.string_set.filter(locale=locale).delete()

		dtd = getParser(self.path)
		dtd.readContents(f)
		for e in dtd:
			try:
				s = self.string_set.get(locale=locale, key=e.key)
				# TODO decide what to do if s.dirty == True
				s.value = e.val
				s.dirty = False
			except String.DoesNotExist:
				s = String(file=self, locale=locale, key=e.key, value=e.val)
			if locale.code == 'en-US':
				s.pre = e.pre_ws + e.pre_comment
				s.post = e.post
			s.save()

	def reconstruct(self, locale):
		if self.path.endswith('.dtd'):
			format = (
				lambda s, t: '%s<!ENTITY %s "%s">%s' % (
					s.pre, s.key, escape(t.value, entities={'"': '&quot;'}), s.post
				)
			)
		else:
			format = lambda s, t: '%s%s = %s%s\n' % (s.pre, s.key, t.value, s.post)

		data = ''
		for s in self.base_string_set:
			try:
				t = self.string_set.get(locale=locale, key=s.key)
			except String.DoesNotExist:
				t = s
			data += format(s, t)
		return data

	class Meta:
		unique_together = ('repo', 'path')


class String(models.Model):
	file = models.ForeignKey('File')
	locale = models.ForeignKey('Locale')
	key = models.CharField(max_length=255)
	value = models.CharField(max_length=255)
	pre = models.CharField(max_length=255, blank=True)
	post = models.CharField(max_length=255, blank=True)
	dirty = models.BooleanField(default=False)

	def __unicode__(self):
		return '%s [%s]' % (self.key, self.locale.code)

	class Meta:
		unique_together = ('file', 'locale', 'key')


class HTMLBlock(models.Model):
	alias = models.CharField(max_length=32, primary_key=True)
	html = models.TextField(blank=True)

	def __unicode__(self):
		return 'HTMLBlock [%s]' % self.alias

	class Meta:
		verbose_name = 'HTML Block'
