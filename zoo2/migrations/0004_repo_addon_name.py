# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0003_auto_20150810_2333'),
    ]

    operations = [
        migrations.AddField(
            model_name='repo',
            name='addon_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
