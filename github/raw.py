import os.path
from httplib import BadStatusLine, HTTPSConnection

_raw_conn = HTTPSConnection('raw.githubusercontent.com')


def get_raw_file(repo, commit_sha, path, is_retry=False):
	path = os.path.join('/', repo, commit_sha, path)
	try:
		print ' '.join(['GET', path])
		_raw_conn.request('GET', path)
		res = _raw_conn.getresponse()
		print ' '.join(['GET', path, str(res.status)])
		response_body = res.read()
		if res.status == 404:
			return None
		return response_body
	except BadStatusLine as ex:
		if is_retry:
			raise ex

		print 'closing connection and trying again'
		_raw_conn.close()
		return get_raw_file(repo, commit_sha, path, is_retry=True)
