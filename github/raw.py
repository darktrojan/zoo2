import os.path
from httplib import HTTPSConnection

_raw_conn = HTTPSConnection('raw.githubusercontent.com')

def get_raw_file(repo, commit_sha, path):
	path = os.path.join('/', repo, commit_sha, path)
	print path
	_raw_conn.request('GET', path)
	res = _raw_conn.getresponse()
	return res.read()
