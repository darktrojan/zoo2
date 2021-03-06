import json
import os
import os.path
from datetime import datetime
from httplib import BadStatusLine, HTTPSConnection

_headers = dict()
_headers['Authorization'] = 'token %s' % os.environ['GITHUB_TOKEN']
_headers['User-Agent'] = 'darktrojan'

_api_conn = HTTPSConnection('api.github.com')


def _do_thing(method, path, body=None, token=None, is_retry=False):
	body_json = None
	if body is not None:
		body_json = json.dumps(body)

	# Use a different user's token if given
	headers = dict(_headers)
	if token is not None and token != '':
		print 'Using a user\'s GitHub token: %.8s' % token
		headers['Authorization'] = 'token %s' % token

	try:
		print ' '.join([method, path])
		_api_conn.request(method, path, headers=headers, body=body_json)
		response = _api_conn.getresponse()
		print ' '.join([method, path, str(response.status)])
		response_body = response.read()
		if response.status / 100 == 4:
			print 'Request:'
			print body_json
			print 'Response:'
			print response_body
			return None
		return json.loads(response_body)
	except BadStatusLine as ex:
		if is_retry:
			raise ex

		print 'closing connection and trying again'
		_api_conn.close()
		return _do_thing(method, path, body, token=token, is_retry=True)


def get_head_commit_sha(repo, branch):
	path = os.path.join('/repos', repo, 'git/refs/heads', branch)
	return _do_thing('GET', path)['object']['sha']


def get_commit_tree_sha(repo, commit_sha):
	path = os.path.join('/repos', repo, 'git/commits', commit_sha)
	return _do_thing('GET', path)['tree']['sha']


def traverse_tree(repo, wanted, tree_sha):
	path = os.path.join('/repos', repo, 'git/trees', tree_sha)
	response = _do_thing('GET', path)

	for f in response['tree']:
		if f['path'] == wanted[0]:
			if len(wanted) > 1 and f['type'] == 'tree':
				return traverse_tree(repo, wanted[1:], f['sha'])
			else:
				return f['sha']

	return None


def get_tree_blobs(repo, tree_sha, prefix=''):
	path = os.path.join('/repos', repo, 'git/trees', tree_sha)
	response = _do_thing('GET', path)

	blobs = list()
	for f in response['tree']:
		if f['type'] == 'blob':
			blobs.append(os.path.join(prefix, f['path']))
		elif f['type'] == 'tree':
			blobs.extend(get_tree_blobs(repo, f['sha'], os.path.join(prefix, f['path'])))

	return blobs


def get_tree_dirs(repo, tree_sha):
	path = os.path.join('/repos', repo, 'git/trees', tree_sha)
	response = _do_thing('GET', path)

	blobs = list()
	for f in response['tree']:
		if f['type'] == 'tree':
			blobs.append(f['path'])

	return blobs


def get_pull_request(repo, pull_id):
	path = os.path.join('/repos', repo, 'pulls', str(pull_id))
	return _do_thing('GET', path)


def branch_exists(repo, branch):
	path = os.path.join('/repos', repo, 'branches', branch)
	return _do_thing('GET', path) is not None


def save_files(repo, base_tree_sha, files):
	path = os.path.join('/repos', repo, 'git/trees')
	body = {
		'tree': [],
		'base_tree': base_tree_sha
	}
	for file_path, file_content in files.iteritems():
		body['tree'].append({
			'path': file_path,
			'mode': '100644',
			'type': 'blob',
			'content': file_content
		})

	return _do_thing('POST', path, body)['sha']


def create_commit(repo, message, tree_sha, parent_sha, author=None):
	path = os.path.join('/repos', repo, 'git/commits')
	body = {
		'message': message,
		'tree': tree_sha,
		'parents': [parent_sha]
	}
	if author is not None:
		author['date'] = datetime.utcnow().isoformat() + 'Z'
		body['author'] = author
	return _do_thing('POST', path, body)['sha']


def update_head_commit_sha(repo, branch, commit_sha, force=False):
	if branch_exists(repo, branch):
		path = os.path.join('/repos', repo, 'git/refs/heads', branch)	
		body = {
			'sha': commit_sha,
			'force': force
		}
		return _do_thing('PATCH', path, body)
	else:
		path = os.path.join('/repos', repo, 'git/refs')
		body = {
			'ref': os.path.join('refs/heads', branch),
			'sha': commit_sha
		}
		return _do_thing('POST', path, body)


def create_pull_request(repo, head, base, title, token=None):
	path = os.path.join('/repos', repo, 'pulls')
	body = {
		'head': head,
		'base': base,
		'title': title,
	}
	return _do_thing('POST', path, body, token=token)['number']


def create_fork(repo):
	existing_repos = _do_thing('GET', '/user/repos')
	for r in existing_repos:
		if r['full_name'] == repo:
			return False

	path = os.path.join('/repos', repo, 'forks')
	_do_thing('POST', path)
	return True


def add_webhook(repo, token):
	path = os.path.join('/repos', repo, 'hooks')
	body = {
		'name': 'web',
		'active': True,
		'events': ['push'],
		'config': {
			'url': '%s/hook' % os.environ['BASE_URL'],
			'content_type': 'json',
			'secret': os.environ['GITHUB_HOOK_SECRET']
		}
	}
	return _do_thing('POST', path, body, token=token)


def get_user_data(token):
	# token must have user:email scope
	data = _do_thing('GET', '/user', token=token)
	for e in _do_thing('GET', '/user/emails', token=token):
		if e['primary']:
			data['primary_email'] = e['email']
			break
	return data
