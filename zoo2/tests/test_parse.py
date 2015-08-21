from django.test import TestCase

from ..models import *


class NoteParseTestCase(TestCase):

	@classmethod
	def setUpTestData(cls):
		cls.u = User(username='foo')
		cls.u.save()
		cls.l = Locale(code='en-US', name='English')
		cls.l.save()
		cls.r = Repo(owner=cls.u)
		cls.r.save()

	def test_parse_no_comments(self):
		f = File(repo=self.r, path='.properties')
		f.save()
		f.parse('foo = bar\n', self.l)

		self.assertEqual(1, String.objects.count())
		self.assertEqual(1, f.string_set.count())

		s = f.string_set.first()
		self.assertEqual('foo', s.key)
		self.assertEqual('bar', s.value)
		self.assertEqual('', s.pre)
		self.assertEqual('', s.post)

	def test_parse_simple_comment(self):
		f = File(repo=self.r, path='.properties')
		f.save()
		f.parse('# woo comment\nfoo = bar\n', self.l)

		self.assertEqual(1, String.objects.count())
		self.assertEqual(1, f.string_set.count())

		s = f.string_set.first()
		self.assertEqual('foo', s.key)
		self.assertEqual('bar', s.value)
		self.assertEqual('# woo comment\n', s.pre)
		self.assertEqual('', s.post)

	def test_parse_complex_comment(self):
		f = File(repo=self.r, path='.properties')
		f.save()
		f.parse('# woo comment\n# woo more comment\nfoo = bar\n', self.l)

		self.assertEqual(1, String.objects.count())
		self.assertEqual(1, f.string_set.count())

		s = f.string_set.first()
		self.assertEqual('foo', s.key)
		self.assertEqual('bar', s.value)
		self.assertEqual('# woo comment\n# woo more comment\n', s.pre)
		self.assertEqual('', s.post)

	def test_parse_example_comment(self):
		# This test is a bit pointless now, but oh well.
		f = File(repo=self.r, path='.properties')
		f.save()
		f.parse('# woo comment\n# @example %S 3\nfoo = %S blind mice\n', self.l)

		self.assertEqual(1, String.objects.count())
		self.assertEqual(1, f.string_set.count())

		s = f.string_set.first()
		self.assertEqual('foo', s.key)
		self.assertEqual('%S blind mice', s.value)
		self.assertEqual('# woo comment\n# @example %S 3\n', s.pre)
		self.assertEqual('', s.post)

	def test_parse_2example_comment(self):
		# This test is a bit pointless now, but oh well.
		f = File(repo=self.r, path='.properties')
		f.save()
		f.parse(
			'# woo comment\n# @example %1$S a herd\n# @example %2$S cows\nfoo = %1$S of %2$S\n',
			self.l
		)

		self.assertEqual(1, String.objects.count())
		self.assertEqual(1, f.string_set.count())

		s = f.string_set.first()
		self.assertEqual('foo', s.key)
		self.assertEqual('%1$S of %2$S', s.value)
		self.assertEqual('# woo comment\n# @example %1$S a herd\n# @example %2$S cows\n', s.pre)
		self.assertEqual('', s.post)
