# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zoo2', '0011_remove_string_example_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='translation',
            name='head_commit',
        ),
    ]
