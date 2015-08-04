from chrome_manifest import ChromeManifestParser
from django.test import TestCase

initial_manifest = '''
locale test en-US locale/en-US/
'''
de_fr_manifest = '''
locale test en-US locale/en-US/
locale test de locale/de/
locale test fr locale/fr/
'''
fr_manifest = '''
locale test en-US locale/en-US/
locale test fr locale/fr/
'''
fr_ptBR_manifest = '''
locale test en-US locale/en-US/
locale test fr locale/fr/
locale test pt-BR locale/pt-BR/
'''
fr_mi_ptBR_manifest = '''
locale test en-US locale/en-US/
locale test fr locale/fr/
locale test mi locale/mi/
locale test pt-BR locale/pt-BR/
'''


class ChromeManifestTestCase(TestCase):

	def test_roundtrip(self):
		parser = ChromeManifestParser(initial_manifest)
		self.assertEqual(len(parser.existing), 1)
		self.assertIn('en-US', parser.existing)
		self.assertEqual(parser.reconstruct(), initial_manifest)

	def test_add_only(self):
		parser = ChromeManifestParser(initial_manifest)
		parser.add_locale('fr')
		self.assertEqual(len(parser.existing), 2)
		self.assertIn('en-US', parser.existing)
		self.assertIn('fr', parser.existing)
		self.assertEqual(parser.reconstruct(), fr_manifest)

	def test_add_before(self):
		parser = ChromeManifestParser(fr_manifest)
		parser.add_locale('de')
		self.assertEqual(len(parser.existing), 3)
		self.assertIn('en-US', parser.existing)
		self.assertIn('fr', parser.existing)
		self.assertIn('de', parser.existing)
		self.assertEqual(parser.reconstruct(), de_fr_manifest)

	def test_add_after(self):
		parser = ChromeManifestParser(fr_manifest)
		parser.add_locale('pt-BR')
		self.assertEqual(len(parser.existing), 3)
		self.assertIn('en-US', parser.existing)
		self.assertIn('fr', parser.existing)
		self.assertIn('pt-BR', parser.existing)
		self.assertEqual(parser.reconstruct(), fr_ptBR_manifest)

	def test_add_between(self):
		parser = ChromeManifestParser(fr_ptBR_manifest)
		parser.add_locale('mi')
		self.assertEqual(len(parser.existing), 4)
		self.assertIn('en-US', parser.existing)
		self.assertIn('pt-BR', parser.existing)
		self.assertIn('fr', parser.existing)
		self.assertIn('mi', parser.existing)
		self.assertEqual(parser.reconstruct(), fr_mi_ptBR_manifest)

	def test_add_again(self):
		parser = ChromeManifestParser(de_fr_manifest)
		parser.add_locale('fr')
		self.assertEqual(len(parser.existing), 3)
		self.assertIn('en-US', parser.existing)
		self.assertIn('fr', parser.existing)
		self.assertIn('de', parser.existing)
		self.assertEqual(parser.reconstruct(), de_fr_manifest)
