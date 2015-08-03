from xml.dom.minidom import parse, parseString

class InstallRDFParser(object):
	def __init__(self, rdf, is_path=False):
		if is_path:
			self.dom = parse(rdf)
		else:
			self.dom = parseString(rdf)

		self.translations = dict()

		locale = 'en-US'
		name = self.dom.getElementsByTagName('em:name')[0].firstChild.data.strip()
		description = self.dom.getElementsByTagName('em:description')[0].firstChild.data.strip()

		self.translations[locale] = { 'name': name, 'description': description }

		for l in self.dom.getElementsByTagName('em:localized'):
			locale = l.getElementsByTagName('em:locale')[0].firstChild.data.strip()
			name = l.getElementsByTagName('em:name')[0].firstChild.data.strip()
			description = l.getElementsByTagName('em:description')[0].firstChild.data.strip()

			self.translations[locale] = { 'name': name, 'description': description, 'element': l }

	def add_locale(self, locale_code, name_str, description_str):
		if locale_code in self.translations:
			localized = self.translations[locale_code]['element']
			name = localized.getElementsByTagName('em:name')[0]
			name.firstChild.data = name_str
			description = localized.getElementsByTagName('em:description')[0]
			description.firstChild.data = description_str
			return

		insert_at_end = True
		for l, t in self.translations.iteritems():
			if l == 'en-US':
				continue

			template = t['element']
			if l > locale_code:
				insert_at_end = False
				break

		localized = template.cloneNode(True)
		locale = localized.getElementsByTagName('em:locale')[0]
		locale.firstChild.data = locale_code
		name = localized.getElementsByTagName('em:name')[0]
		name.firstChild.data = name_str
		description = localized.getElementsByTagName('em:description')[0]
		description.firstChild.data = description_str

		before = template.previousSibling
		after = template.nextSibling if insert_at_end else before
		parent = template.parentNode
		parent.insertBefore(before.cloneNode(False), after)
		parent.insertBefore(localized, after)

		self.translations[locale_code] = { 'name': name_str, 'description': description_str, 'element': localized }

	def reconstruct(self):
		return self.dom.toxml('utf-8').replace('?><', '?>\n<')

if __name__ == '__main__':
	i = InstallRDFParser(
		'/home/geoff/firefoxprofiles/sjua7g0g.test/extensions/menufilter@darktrojan.net/install.rdf', is_path=True
	)
	# i.add_locale('ab-CD', 'name in test', 'description in test')
	i.add_locale('fr', 'name in french', 'description in french')
	print [l for l in i.translations.iterkeys()]
	# i.add_locale('uk', 'name in ukrainian', 'description in ukrainian')
	# i.add_locale('mi', 'name in maori', 'description in maori')
	i.add_locale('fr', 'name in french, but changed', 'description in french, but changed')
	print i.reconstruct()
	print [l for l in i.translations.iterkeys()]
