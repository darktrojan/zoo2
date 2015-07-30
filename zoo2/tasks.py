from __future__ import absolute_import

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zoo2.settings')

from celery import Celery
from django.conf import settings

from github import api
from zoo2.models import *

app = Celery('zoo2', broker='django://')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task
def download_translation(translation_pk, use_fork=False):
	t = Translation.objects.get(pk=translation_pk)
	t.download_from_source(use_fork)

@app.task
def save_translation(translation_pk):
	t = Translation.objects.get(pk=translation_pk)
	print 'Saving to GitHub'
	t.save_to_github()
	print 'Creating pull request'
	original = t.pull_request
	t.create_pull_request()
	if t.pull_request == original:
		print 'Already had a pull request'
	else:
		print 'New pull request: ' + t.pull_request
