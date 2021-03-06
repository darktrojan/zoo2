import hashlib
import hmac
import httplib
import json
import os.path
import re
import uuid
from collections import OrderedDict
from urllib import urlencode

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from github import auth
from zoo2.models import *
from zoo2 import tasks


def _create_absolute_url(request, path):
	scheme = 'https' if os.environ.get('HTTPS') == 'on' else 'http'
	return '%s://%s%s' % (scheme, request.get_host(), path)


def index(request):
	user_translations = []
	if request.user.is_authenticated():
		user_translations = request.user.translation_set.all().order_by(
			'repo__addon_name', 'locale__name'
		)
	return render(request, 'index.html', {
		'repos': Repo.objects.all().order_by('addon_name'),
		'translation_count': len(set([t.locale.code for t in Translation.objects.all()])),
		'user_translations': user_translations
	})


def log_out(request):
	logout(request)
	response = HttpResponseRedirect(_create_absolute_url(request, '/'))
	response.delete_cookie('persona_email')
	return response


@csrf_exempt
@require_http_methods(['POST'])
def hook(request):
	secret = os.environ['GITHUB_HOOK_SECRET']
	theirs = request.META['HTTP_X_HUB_SIGNATURE']
	ours = 'sha1=' + hmac.new(secret, request.body, hashlib.sha1).hexdigest()

	valid = False
	try:
		valid = hmac.compare_digest(theirs, ours)
	except AttributeError:
		# hmac.compare_digest doesn't exist in Python 2.7.6
		valid = theirs == ours

	if not valid:
		return HttpResponse('Stop.', status=httplib.INTERNAL_SERVER_ERROR, content_type='text/plain')

	body = json.loads(request.body)
	repo = get_object_or_404(Repo, full_name=body['repository']['full_name'])

	if request.META['HTTP_X_GITHUB_EVENT'] == 'ping':
		return HttpResponse('Pong!', content_type='text/plain')

	ref = body['ref']
	if ref != os.path.join('refs/heads', repo.branch):
		return HttpResponse('Not for me.', status=httplib.ACCEPTED, content_type='text/plain')

	tasks.update_repo_from_upstream.delay(repo.pk, body['head_commit']['id'], body['commits'])

	return HttpResponse('Okay, got it.', status=httplib.CREATED, content_type='text/plain')


def profile(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect(_create_absolute_url(request, '/'))

	original_username = request.user.username
	error_message = None
	if request.method == 'POST':
		username = request.POST.get('username')
		if len(username) < 4:
			error_message = 'Please choose a longer username.'
		else:
			try:
				if original_username != username:
					request.user.username = username
					request.user.save()
				request.session['confirm_message'] = 'Your new username was successfully saved.'
				return HttpResponseRedirect(_create_absolute_url(request, reverse('profile')))
			except IntegrityError:
				request.user.username = original_username
				error_message = 'That username appears to be in user. Please choose another.'

	return render(request, 'profile.html', {
		'error_message': error_message,
		'confirm_message': request.session.pop('confirm_message', None)
	})


@csrf_exempt
@require_http_methods(['POST'])
def persona_auth(request):
	assertion = request.POST['assertion']
	user = authenticate(assertion=assertion, audience=request.META['HTTP_HOST'])
	if user is not None:
		login(request, user)
		response = HttpResponse('logged in')
		response.set_cookie('persona_email', user.email)
		return response
	else:
		return HttpResponse('not logged in')


def github_auth(request):
	if 'code' not in request.GET or 'state' not in request.GET:
		state = str(uuid.uuid4())
		request.session['state'] = state
		request.session['referer'] = request.META.get('HTTP_REFERER')
		return HttpResponseRedirect(
			'https://github.com/login/oauth/authorize?' + urlencode({
				'client_id': os.environ['GITHUB_CLIENT_ID'],
				'state': state,
				'scope': ','.join(['public_repo', 'user:email'])
			})
		)

	code = request.GET['code']
	state = request.GET['state']
	if state != request.session.pop('state'):
		return HttpResponse(status=httplib.UNAUTHORIZED)

	token = auth.get_access_token(code, state)['access_token']

	if request.user.is_authenticated():
		# TODO what if this GitHub user is linked to a different account here?
		auth.save_to_profile(request.user, token)
	else:
		user = authenticate(token=token)
		login(request, user)

	go_to = request.session.pop('referer')
	if go_to is None:
		go_to = _create_absolute_url(request, '/')

	return HttpResponseRedirect(go_to)


# repo_patterns
def repo(request, full_name):
	repo = get_object_or_404(Repo, full_name=full_name)
	translated = OrderedDict(
		(t.locale.code, t) for t in repo.translation_set.all().order_by('locale__name')
	)
	return render(request, 'repo.html', {
		'repo': repo,
		'locales': Locale.objects.all().order_by('name'),
		'translated': translated
	})


@require_http_methods(['POST'])
@login_required
def new(request, full_name):
	repo = get_object_or_404(Repo, full_name=full_name)
	code = request.POST.get('locale')
	locale = Locale.objects.get(code=code)
	translation = Translation(repo=repo, locale=locale, owner=request.user)
	try:
		translation.save()
		if code in repo.translations_list_set:
			# pretend to be busy until we're actually busy
			translation.busy = 1
			translation.save(update_fields=['busy'])
			tasks.download_translation.delay(translation.pk)
	except IntegrityError:
		# TODO
		return HttpResponse(status=httplib.INTERNAL_SERVER_ERROR)

	return HttpResponseRedirect(
		_create_absolute_url(request, translation.get_absolute_url())
	)


# translation_pattens
def translation(request, full_name, code):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)
	is_owner = translation.is_owner(request.user)

	counts = OrderedDict()
	for f in repo.file_set.all().order_by('path'):
		counts[f.path] = {
			'counts': f.get_complete_counts(locale),
			'dirty': f.has_dirty_strings(locale)
		}

	return render(request, 'translation.html', {
		'repo': repo,
		'locale': locale,
		'translation': translation,
		'counts': counts,
		'is_owner': is_owner,
		'fileaction': 'edit' if is_owner else 'view',
		'confirm_message': request.session.pop('confirm_message', None)
	})


def file(request, full_name, code, path, fileaction):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)
	is_owner = translation.is_owner(request.user)

	if not is_owner and fileaction != 'view':
		return HttpResponseRedirect(
			_create_absolute_url(request, reverse('view', args=([full_name, code, path])))
		)

	file = get_object_or_404(File, repo=repo, path=path)
	string_set = file.string_set.filter(locale=Locale.objects.get(code='en-US')).order_by('pk')

	strings = list()
	for s in string_set:
		dirty = False
		pre = []
		example_data = []
		pluralrule = False
		plurals = None
		for line in s.pre.splitlines():
			line = line.strip()
			line = re.sub('^(#|<!--)\s*', '', line)
			if line.startswith('@example '):
				example_data.append(line[9:].split(None, 1))
				continue
			if line.startswith('@pluralrule'):
				pluralrule = True
				continue
			if line.startswith('@plurals '):
				plurals = line[9:]
				continue
			line = re.sub('\s*-->$', '', line)
			pre.append(line)
		try:
			ts = file.string_set.get(locale=locale, key=s.key)
			t = ts.value
			dirty = ts.dirty
		except String.DoesNotExist:
			t = ''
		strings.append({
			'pre': '\n'.join(pre).strip(),
			'example_data': urlencode(dict(example_data)),
			'pluralrule': pluralrule,
			'plurals': plurals,
			'base': s,
			'translated': t,
			'dirty': dirty
		})

	return render(request, 'file.html', {
		'translation': translation,
		'repo': repo,
		'locale': locale,
		'file': file,
		'strings': strings,
		'is_owner': is_owner,
		'fileaction': fileaction
	})


@require_http_methods(['POST'])
def save(request, full_name, code, path):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)

	if not translation.is_owner(request.user):
		return HttpResponse(status=httplib.UNAUTHORIZED)

	file = get_object_or_404(File, repo=repo, path=path)
	strings = file.string_set.filter(locale=Locale.objects.get(code='en-US'))

	translation_dirty = False
	for s in strings:
		t = request.POST.get('locale_strings[%s]' % s.key)
		try:
			o = file.string_set.get(locale=locale, key=s.key)
		except String.DoesNotExist:
			o = String(file=file, locale=locale, key=s.key)
			o.save()

		if o.value != t:
			o.value = t
			o.dirty = True
			o.save(update_fields=['value', 'dirty'])
			translation_dirty = True

		if translation_dirty:
			translation.dirty = True
			translation.save(update_fields=['dirty'])

	return HttpResponseRedirect(
		_create_absolute_url(request, translation.get_absolute_url())
	)


@require_http_methods(['POST'])
def push(request, full_name, code):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)

	if not translation.is_owner(request.user):
		return HttpResponse(status=httplib.UNAUTHORIZED)

	tasks.save_translation.delay(translation.pk)

	request.session['confirm_message'] = 'Pull request created.'
	return HttpResponseRedirect(_create_absolute_url(request, translation.get_absolute_url()))
