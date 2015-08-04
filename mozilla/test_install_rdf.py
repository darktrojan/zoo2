import os.path
from install_rdf import InstallRDFParser
from django.test import TestCase


def get_fixture(filename):
	with open(os.path.join(os.path.dirname(__file__), 'fixtures', filename)) as f:
		return f.read()


class InstallRDFTestCase(TestCase):

	def test_roundtrip(self):
		initial = get_fixture('initial.rdf')
		parser = InstallRDFParser(initial)
		self.assertEqual(parser.indentation, '\t')
		self.assertEqual(len(parser.translations), 1)
		self.assertIn('en-US', parser.translations)
		self.assertEqual(parser.reconstruct(), initial)

	def test_add_only(self):
		initial = get_fixture('initial.rdf')
		expected = get_fixture('fr.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('fr', 'Name in French', 'Description in French')
		self.assertEqual(parser.reconstruct(), expected)

	def test_add_before(self):
		initial = get_fixture('fr.rdf')
		expected = get_fixture('de_fr.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('de', 'Name in German', 'Description in German')
		self.assertEqual(parser.reconstruct(), expected)

	def test_add_after(self):
		initial = get_fixture('fr.rdf')
		expected = get_fixture('fr_nl.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('nl', 'Name in Dutch', 'Description in Dutch')
		self.assertEqual(parser.reconstruct(), expected)

	def test_add_between(self):
		initial = get_fixture('de_fr.rdf')
		expected = get_fixture('de_es_fr.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('es', 'Name in Spanish', 'Description in Spanish')
		self.assertEqual(parser.reconstruct(), expected)

	def test_add_changed(self):
		initial = get_fixture('fr.rdf')
		expected = get_fixture('fr_changed.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('fr', 'Name in French, changed', 'Description in French, changed')
		self.assertEqual(parser.reconstruct(), expected)

	def test_roundtrip_spaces(self):
		initial = get_fixture('initial_spaces.rdf')
		parser = InstallRDFParser(initial)
		self.assertEqual(parser.indentation, '  ')
		self.assertEqual(len(parser.translations), 1)
		self.assertIn('en-US', parser.translations)
		self.assertEqual(parser.reconstruct(), initial)

	def test_add_only_spaces(self):
		initial = get_fixture('initial_spaces.rdf')
		expected = get_fixture('fr_spaces.rdf')
		parser = InstallRDFParser(initial)
		parser.add_locale('fr', 'Name in French', 'Description in French')
		self.assertEqual(parser.reconstruct(), expected)
