# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0008_translation_busy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translation',
            name='busy',
            field=models.IntegerField(default=0),
        ),
    ]
