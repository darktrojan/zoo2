import json
import os
from httplib import BadStatusLine, HTTPSConnection
from urllib import urlencode
from . import api

from django.contrib.auth.models import User

from zoo2.models import UserProfile

_api_conn = HTTPSConnection('github.com')
_headers = dict()
_headers['Accept'] = 'application/json'


def _do_thing(method, path, body, is_retry=False):
	try:
		print path
		_api_conn.request(method, path, headers=_headers, body=urlencode(body))
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
		'client_id': os.environ['GITHUB_CLIENT_ID'],
		'client_secret': os.environ['GITHUB_CLIENT_SECRET'],
		'code': code,
		'state': state
	}
	print body
	return _do_thing('POST', '/login/oauth/access_token', body)


def save_to_profile(user, token, user_data=None):
	try:
		profile = user.profile
	except UserProfile.DoesNotExist:
		profile = UserProfile(user=user)

	if user_data is None:
		# TODO what if this fails?
		user_data = api.get_user_data(token)

	profile.github_username = user_data['login']
	profile.github_token = token
	profile.save()


class GitHubBackend(object):
	def authenticate(self, token):
		user_data = api.get_user_data(token)
		if user_data is None:
			return None

		try:
			profile = UserProfile.objects.get(github_username=user_data['login'])
			profile.github_token = token
			profile.save(update_fields=['github_token'])
			return profile.user
		except UserProfile.DoesNotExist:
			# TODO what if this username is used already?
			user = User(
				username=user_data['login'], password='github login', email=user_data['primary_email']
			)
			user.save()
			save_to_profile(user, token, user_data)
			return user

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
