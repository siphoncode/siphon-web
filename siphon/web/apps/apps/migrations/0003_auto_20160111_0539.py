# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0002_app_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseversion',
            name='comment',
            field=models.TextField(help_text='User-facing notes about which native modules are available in this base_version and any other useful information.', blank=True),
        ),
        migrations.AddField(
            model_name='baseversion',
            name='react_native_version',
            field=models.CharField(max_length=32, help_text='React Native release that this base_version is tied to e.g. "0.18.0"', default='CHANGEME'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='baseversion',
            name='latest',
            field=models.BooleanField(help_text='Signals the currently active base_version that newly created Siphon apps will be assigned automatically. Note that setting this flag to True will turn it off for the currently active model so that this is the only one.', default=False),
        ),
        migrations.AlterField(
            model_name='baseversion',
            name='name',
            field=models.CharField(help_text='The base_version itself e.g. "0.1"', max_length=32),
        ),
    ]
