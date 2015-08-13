# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0004_repo_addon_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='HTMLBlock',
            fields=[
                ('alias', models.CharField(max_length=32, serialize=False, primary_key=True)),
                ('html', models.TextField()),
            ],
        ),
    ]
