import os.path

def parse(manifest):
	existing = []
	locale_path = None

	for line in manifest.splitlines():
		if line.startswith('locale'):
			parts = line.split()
			existing.append(parts[2])
			if parts[2] == 'en-US':
				locale_path = os.path.dirname(parts[3].rstrip('/'))

	return locale_path, existing
