import json, os.path

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from zoo2.models import *

def repo(request, full_name):
	repo = get_object_or_404(Repo, full_name=full_name)
	return render(request, 'repo.html', { 'repo': repo })

def locale(request, full_name, code):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	return render(request, 'locale.html', { 'repo': repo, 'locale': locale })

def file(request, full_name, code, path):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	file = get_object_or_404(File, repo=repo, path=path)
	strings = file.string_set.filter(locale=Locale.objects.get(code='en-US')).order_by('pk')

	translation = list()
	for s in strings:
		try:
			t = file.string_set.get(locale=locale, key=s.key).value
		except String.DoesNotExist:
			t = ''
		translation.append({
			'base': s,
			'translated': t,
		})

	return render(request, 'file.html', {
		'repo': repo,
		'locale': locale,
		'file': file,
		'strings': translation,
		# 'reconstructed': file.reconstruct(locale)
	})

@require_http_methods(['POST'])
def save(request, full_name, code, path):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	file = get_object_or_404(File, repo=repo, path=path)
	strings = file.string_set.filter(locale=Locale.objects.get(code='en-US'))

	for s in strings:
		t = request.POST.get('locale_strings[%s]' % s.key)
		try:
			o = file.string_set.get(locale=locale, key=s.key)
		except String.DoesNotExist:
			o = String(file=file, locale=locale, key=s.key)
		o.value = t
		o.save()

	return HttpResponse('ok saved it')

@csrf_exempt
@require_http_methods(['POST'])
def hook(request):
	# TODO hash requests with secret
	body = json.loads(request.body)
	repo = get_object_or_404(Repo, full_name=body['repository']['full_name'])

	if request.META['HTTP_X_GITHUB_EVENT'] == 'ping':
		return HttpResponse('Pong!', content_type='text/plain')

	ref = body['ref']
	if ref != os.path.join('refs/heads', repo.branch):
		return HttpResponse('Not for me.', status=202, content_type='text/plain')

	repo.update_fork(body['head_commit']['id'])

	# TODO update database with changed strings

	return HttpResponse('Okay, got it.', status=201, content_type='text/plain')
