import json, os.path, re

from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from zoo2.models import *
from zoo2 import tasks

def index(request):
	return render(request, 'index.html', { 'repos': Repo.objects.all() })

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

# repo_patterns

def repo(request, full_name):
	repo = get_object_or_404(Repo, full_name=full_name)
	return render(request, 'repo.html', {
		'repo': repo,
		'locales': Locale.objects.all()
	})

@require_http_methods(['POST'])
def new(request, full_name):
	repo = get_object_or_404(Repo, full_name=full_name)
	code = request.POST.get('locale')
	locale = Locale.objects.get(code=code)
	translation = Translation(repo=repo, locale=locale)
	try:
		translation.save()
	except IntegrityError:
		return HttpResponse('oops')

	return HttpResponseRedirect(reverse('translation', args=(full_name, code)))

# translation_pattens

def translation(request, full_name, code):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)

	counts = dict()
	for f in repo.file_set.all():
		counts[f.path] = {
			'counts': f.get_complete_counts(locale),
			'dirty': f.has_dirty_strings(locale)
		}

	return render(request, 'translation.html', {
		'repo': repo,
		'locale': locale,
		'translation': translation,
		'counts': counts
	})

@require_http_methods(['POST'])
def push(request, full_name, code):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	translation = get_object_or_404(Translation, repo=repo, locale=locale)

	tasks.save_translation.delay(translation.pk)

	return HttpResponse('ok pushing it', status=201)

def edit(request, full_name, code, path):
	repo = get_object_or_404(Repo, full_name=full_name)
	locale = get_object_or_404(Locale, code=code)
	file = get_object_or_404(File, repo=repo, path=path)
	strings = file.string_set.filter(locale=Locale.objects.get(code='en-US')).order_by('pk')

	translation = list()
	for s in strings:
		dirty = False
		s.pre = s.pre.strip()
		s.pre = re.sub('^(#|<!--)\s*', '', s.pre)
		s.pre = re.sub('\s*-->\s*$', '', s.pre)
		try:
			ts = file.string_set.get(locale=locale, key=s.key)
			t = ts.value
			dirty = ts.dirty
		except String.DoesNotExist:
			t = ''
		translation.append({
			'base': s,
			'translated': t,
			'dirty': dirty
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
	translation = get_object_or_404(Translation, repo=repo, locale=locale)
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

	return HttpResponseRedirect(reverse('translation', args=(full_name, code)))
