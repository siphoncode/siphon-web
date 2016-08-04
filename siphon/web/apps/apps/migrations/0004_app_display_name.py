# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0003_auto_20160111_0539'),
    ]

    operations = [
        migrations.AddField(
            model_name='app',
            name='display_name',
            field=models.CharField(max_length=32, blank=True),
        ),
    ]
