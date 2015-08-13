# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0005_htmlblock'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='htmlblock',
            options={'verbose_name': 'HTML Block'},
        ),
        migrations.AddField(
            model_name='repo',
            name='amo_stub',
            field=models.CharField(max_length=32, verbose_name=b'AMO stub', blank=True),
        ),
        migrations.AlterField(
            model_name='htmlblock',
            name='html',
            field=models.TextField(blank=True),
        ),
    ]
