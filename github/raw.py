import os.path
from httplib import HTTPSConnection


def get_raw_file(repo, commit_sha, path):
	raw_conn = HTTPSConnection('raw.githubusercontent.com')
	path = os.path.join('/', repo, commit_sha, path)

	print ' '.join(['GET', path])
	raw_conn.request('GET', path)
	res = raw_conn.getresponse()
	print ' '.join(['GET', path, str(res.status)])
	response_body = res.read()
	if res.status == 404:
		return None
	return response_body
