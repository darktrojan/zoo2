import json, os
from httplib import BadStatusLine, HTTPSConnection

_api_conn = HTTPSConnection('github.com')
_headers = dict()
_headers['Accept'] = 'application/json'

def _do_thing(method, path, body=None, is_retry=False):
	body_json = None
	if body is not None:
		body_json = json.dumps(body)

	try:
		print path
		_api_conn.request(method, path, headers=_headers, body=body_json)
		response = _api_conn.getresponse()
		print response.status
		response_body = response.read()
		if response.status / 100 == 4:
			print response_body
			return None
		return json.loads(response_body)
	except BadStatusLine as ex:
		if is_retry:
			raise ex

		print 'closing connection and trying again'
		_api_conn.close()
		return _do_thing(method, path, body, is_retry=True)

def get_access_token(code, state):
	body = {
		'client_id': '7d5bd4b7b4ee040275ba',
		'client_secret': os.environ['GITHUB_CLIENT_SECRET'],
		'code': code,
		'state': state
	}
	return _do_thing('POST', '/login/oauth/access_token')
