import json
from httplib import BadStatusLine, HTTPSConnection
from urllib import urlencode

from django.contrib.auth.models import User

_api_conn = HTTPSConnection('verifier.login.persona.org')
_headers = {
	'Content-Type': 'application/x-www-form-urlencoded'
}

def _do_thing(method, path, body=None, is_retry=False):
	try:
		print path
		_api_conn.request(method, path, headers=_headers, body=urlencode(body))
		response = _api_conn.getresponse()
		print response.status
		response_body = response.read()
		return json.loads(response_body)
	except BadStatusLine as ex:
		if is_retry:
			raise ex

		print 'closing connection and trying again'
		_api_conn.close()
		return _do_thing(method, path, body, is_retry=True)

class PersonaBackend(object):
	def authenticate(self, assertion, audience):
		body = {
			'assertion': assertion,
			'audience': audience
		}
		data = _do_thing('POST', '/verify', body=body)
		if data['status'] == 'okay':
			email = data['email']
			try:
				user = User.objects.get(email=email)
			except User.DoesNotExist:
				user = User(username=email, password='persona login', email=email)
				user.save()
			return user

		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
