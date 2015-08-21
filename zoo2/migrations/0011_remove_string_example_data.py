# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0010_string_example_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='string',
            name='example_data',
        ),
    ]
