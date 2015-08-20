# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0009_auto_20150818_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='string',
            name='example_data',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
