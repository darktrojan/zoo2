from __future__ import absolute_import

import os.path
from xml.sax.saxutils import escape

from django.db import models

from github import api, raw
from mozilla.parser import getParser

class Locale(models.Model):
	code = models.CharField(max_length=5, primary_key=True)
	name = models.CharField(max_length=32)

	def __unicode__(self):
		return '%s [%s]' % (self.name, self.code)


class Repo(models.Model):
	full_name = models.CharField(max_length=255)
	locale_path = models.CharField(max_length=255)
	translations = models.ManyToManyField(Locale, through='Translation')
	branch = models.CharField(max_length=255)
	head_commit = models.CharField(max_length=40)

	def __unicode__(self):
		return self.full_name

	def _get_fork_name(self):
		return os.path.join('darktrojan-test', self.full_name.split('/', 2)[1])
	fork_name = property(_get_fork_name)

	def find_files(self):
		if self.head_commit == '':
			self.head_commit = api.get_head_commit_sha(self.full_name, self.branch)
			self.save(update_fields=['head_commit'])
		tree_sha = api.get_commit_tree_sha(self.full_name, self.head_commit)
		leaf = api.traverse_tree(self.full_name, os.path.join(self.locale_path, 'en-US').split('/'), tree_sha)
		blobs = api.get_tree_blobs(self.full_name, leaf['sha'])

		for b in blobs:
			f = File(repo=self, path=b)
			f.save()

	def update_fork(self, new_head_commit):
		api.update_head_commit_sha(self.fork_name, 'zoo2', new_head_commit, force=True)
		self.head_commit = new_head_commit
		self.save(update_fields=['head_commit'])


class Translation(models.Model):
	locale = models.ForeignKey(Locale)
	repo = models.ForeignKey(Repo)
	head_commit = models.CharField(max_length=40)
	pull_request = models.IntegerField()

	def __unicode__(self):
		return '%s [%s]' % (self.repo.full_name, self.branch_name)

	def _get_branch_name(self):
		return 'zoo2_%s' % self.locale.code
	branch_name = property(_get_branch_name)

	def download_from_source(self, use_fork=False):
		for f in self.repo.file_set.all():
			f.download_from_source(self.locale, use_fork=use_fork)

	def save_to_github(self):
		files = dict()
		for f in self.repo.file_set.all():
			path = os.path.join(self.repo.locale_path, self.locale.code, f.path)
			content = f.reconstruct(self.locale)
			files[path] = content

		if self.head_commit is None:
			parent_commit = self.repo.head_commit
		else:
			parent_commit = self.head_commit

		tree_sha = api.get_commit_tree_sha(self.repo.fork_name, parent_commit)
		tree_sha = api.save_files(self.repo.fork_name, tree_sha, files)
		message = 'Update %s translation' % self.locale.name
		self.head_commit = api.create_commit(self.repo.fork_name, message, tree_sha, parent_commit)

		api.update_head_commit_sha(self.repo.fork_name, self.branch_name, self.head_commit, force=True)
		self.save(update_fields=['head_commit'])

	def create_pull_request(self):
		if self.pull_request > 0:
			pr = api.get_pull_request(self.repo.full_name, self.pull_request)
			if pr is not None and pr['state'] == 'open':
				return

		head = 'darktrojan-test:%s' % self.branch_name
		title = 'Update %s translation' % self.locale.name
		self.pull_request = api.create_pull_request(self.repo.full_name, head, self.repo.branch, title)
		self.save(update_fields=['pull_request'])


class File(models.Model):
	repo = models.ForeignKey('Repo')
	path = models.CharField(max_length=255)

	def __unicode__(self):
		return '%s %s' % (self.repo.full_name, self.path)

	def get_full_path(self, locale):
		return os.path.join(self.repo.locale_path, locale.code, self.path)

	def download_from_source(self, locale, use_fork=False):
		repo_name = self.repo.full_name if not use_fork else self.repo.fork_name
		f = raw.get_raw_file(repo_name, self.repo.head_commit, self.get_full_path(locale))

		dtd = getParser(self.path)
		dtd.readContents(f)
		for e in dtd:
			try:
				s = self.string_set.filter(locale=locale, key=e.key)
				s.value = e.val
			except String.DoesNotExist:
				s = String(file=self, locale=locale, key=e.key, value=e.val)
			if locale.code == 'en-US':
				s.pre = e.pre_ws + e.pre_comment
				s.post = e.post
			s.save()

	def reconstruct(self, locale):
		if self.path.endswith('.dtd'):
			format = lambda s, t: '%s<!ENTITY %s "%s">%s' % (s.pre, s.key, escape(t.value, entities={'"': '&quot;'}), s.post)
		else:
			format = lambda s, t: '%s%s = %s%s\n' % (s.pre, s.key, t.value, s.post)

		data = ''
		for s in self.string_set.filter(locale='en-US').order_by('pk'):
			try:
				t = self.string_set.get(locale=locale, key=s.key)
			except String.DoesNotExist:
				t = s
			data += format(s, t)
		return data


class String(models.Model):
	file = models.ForeignKey('File')
	locale = models.ForeignKey('Locale')
	key = models.CharField(max_length=255)
	value = models.CharField(max_length=255)
	pre = models.CharField(max_length=255, blank=True)
	post = models.CharField(max_length=255, blank=True)

	def __unicode__(self):
		return '%s [%s]' % (self.key, self.locale.code)

	class Meta:
		unique_together = ('file', 'locale', 'key')
