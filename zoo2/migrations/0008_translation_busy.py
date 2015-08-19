# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0007_repo_readme'),
    ]

    operations = [
        migrations.AddField(
            model_name='translation',
            name='busy',
            field=models.BooleanField(default=False),
        ),
    ]
