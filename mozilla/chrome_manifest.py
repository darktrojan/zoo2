import os.path


class ChromeManifestParser(object):
	def __init__(self, manifest):
		self.lines = manifest.splitlines(True)
		self.existing = []
		self.locale_path = None

		for line in self.lines:
			if line.startswith('locale'):
				parts = line.split()
				self.existing.append(parts[2])
				if parts[2] == 'en-US':
					self.locale_line = line
					self.locale_path = os.path.dirname(parts[3].rstrip('/'))

	def reconstruct(self):
		return ''.join(self.lines)

	def add_locale(self, locale_code):
		if locale_code in self.existing:
			return

		self.existing.append(locale_code)
		new_line = self.locale_line.replace('en-US', locale_code)

		index = -1
		for line in self.lines:
			index += 1
			if line.startswith('locale'):
				parts = line.split()
				if parts[2] != 'en-US' and parts[2] > locale_code:
					self.lines.insert(index, new_line)
					return

		index = len(self.lines) + 1
		reverse = self.lines[:]
		reverse.reverse()
		for line in reverse:
			index -= 1
			if line.startswith('locale'):
				self.lines.insert(index, new_line)
				return

		self.lines.append(new_line)
