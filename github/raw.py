import os.path
from httplib import BadStatusLine, HTTPSConnection

_raw_conn = HTTPSConnection('raw.githubusercontent.com')

def get_raw_file(repo, commit_sha, path, is_retry=False):
	path = os.path.join('/', repo, commit_sha, path)
	print path
	try:
		_raw_conn.request('GET', path)
		res = _raw_conn.getresponse()
		return res.read()
	except BadStatusLine as ex:
		if is_retry:
			raise ex

		print 'closing connection and trying again'
		_api_conn.close()
		return _do_thing(method, path, body, is_retry=True)
