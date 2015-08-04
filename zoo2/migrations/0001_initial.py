# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Locale',
            fields=[
                ('code', models.CharField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('full_name', models.CharField(unique=True, max_length=255)),
                ('locale_path', models.CharField(max_length=255)),
                ('translations_list', models.CharField(max_length=255, blank=True)),
                ('branch', models.CharField(max_length=255)),
                ('head_commit', models.CharField(max_length=40)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='String',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('pre', models.CharField(max_length=255, blank=True)),
                ('post', models.CharField(max_length=255, blank=True)),
                ('dirty', models.BooleanField(default=False)),
                ('file', models.ForeignKey(to='zoo2.File')),
                ('locale', models.ForeignKey(to='zoo2.Locale')),
            ],
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('head_commit', models.CharField(max_length=40, blank=True)),
                ('pull_request', models.IntegerField(default=0)),
                ('dirty', models.BooleanField(default=False)),
                ('locale', models.ForeignKey(to='zoo2.Locale')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('repo', models.ForeignKey(to='zoo2.Repo')),
            ],
        ),
        migrations.AddField(
            model_name='file',
            name='repo',
            field=models.ForeignKey(to='zoo2.Repo'),
        ),
        migrations.AlterUniqueTogether(
            name='translation',
            unique_together=set([('repo', 'locale')]),
        ),
        migrations.AlterUniqueTogether(
            name='string',
            unique_together=set([('file', 'locale', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='file',
            unique_together=set([('repo', 'path')]),
        ),
    ]
