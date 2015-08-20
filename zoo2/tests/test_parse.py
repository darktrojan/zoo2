from urlparse import parse_qs

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
		self.assertEqual('', s.example_data)

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
		self.assertEqual('', s.example_data)

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
		self.assertEqual('', s.example_data)

	def test_parse_example_comment(self):
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
		self.assertEqual('%25S=3', s.example_data)
		example_data = parse_qs(s.example_data)
		self.assertEqual('3', example_data['%S'][0])

	def test_parse_2example_comment(self):
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
		self.assertEqual('%251%24S=a+herd&%252%24S=cows', s.example_data)
		example_data = parse_qs(s.example_data)
		self.assertEqual('a herd', example_data['%1$S'][0])
		self.assertEqual('cows', example_data['%2$S'][0])
