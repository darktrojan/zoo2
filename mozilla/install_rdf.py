from xml.dom.minidom import parse, parseString


# TODO this isn't namespace-aware
class InstallRDFParser(object):
	def __init__(self, rdf, is_path=False):
		if is_path:
			self.dom = parse(rdf)
		else:
			self.dom = parseString(rdf)

		first_whitespace = self.dom.documentElement.firstChild.data
		self.indentation = first_whitespace.lstrip('\n')

		self.translations = dict()

		locale = 'en-US'
		name = self.dom.getElementsByTagName('em:name')[0].firstChild.data.strip()
		description = self.dom.getElementsByTagName('em:description')[0].firstChild.data.strip()

		self.translations[locale] = {'name': name, 'description': description}

		for l in self.dom.getElementsByTagName('em:localized'):
			locale = l.getElementsByTagName('em:locale')[0].firstChild.data.strip()
			name = l.getElementsByTagName('em:name')[0].firstChild.data.strip()
			description = l.getElementsByTagName('em:description')[0].firstChild.data.strip()

			self.translations[locale] = {'name': name, 'description': description, 'element': l}

	def add_locale(self, locale_code, name_str, description_str):
		if locale_code in self.translations:
			localized = self.translations[locale_code]['element']
			name = localized.getElementsByTagName('em:name')[0]
			name.firstChild.data = name_str
			description = localized.getElementsByTagName('em:description')[0]
			description.firstChild.data = description_str
			return

		elements = [
			('em:locale', locale_code),
			('em:name', name_str),
			('em:description', description_str)
		]
		template = None
		insert_at_end = True
		for c, t in self.translations.iteritems():
			if c == 'en-US':
				continue

			template = t['element']
			if c > locale_code:
				insert_at_end = False
				break

		if template is None:
			localized = self.dom.createElement('em:localized')
			localized.appendChild(self._create_whitespace(1, 3))
			rdf_description = self.dom.createElement('Description')
			localized.appendChild(rdf_description)

			for k, v in elements:
				element = self.dom.createElement(k)
				element.appendChild(self.dom.createTextNode(v))
				rdf_description.appendChild(self._create_whitespace(1, 4))
				rdf_description.appendChild(element)

			rdf_description.appendChild(self._create_whitespace(1, 3))
			localized.appendChild(self._create_whitespace(1, 2))

			parent = self.dom.getElementsByTagName('Description')[0]
			before = self._create_whitespace(2, 2)
			after = parent.lastChild
		else:
			localized = template.cloneNode(True)
			for k, v in elements:
				element = localized.getElementsByTagName(k)[0]
				if element.firstChild is not None:
					element.firstChild.data = v
				else:
					element.appendChild(self.dom.createTextNode(v))

			parent = template.parentNode
			before = template.previousSibling
			after = template.nextSibling if insert_at_end else before

		parent.insertBefore(before.cloneNode(False), after)
		parent.insertBefore(localized, after)

		self.translations[locale_code] = {
			'name': name_str, 'description': description_str, 'element': localized
		}

	def _create_whitespace(self, lines, indents):
		return self.dom.createTextNode('\n' * lines + self.indentation * indents)

	def reconstruct(self):
		return self.dom.toxml('utf-8').replace('?><', '?>' + '\n' + '<') + '\n'
