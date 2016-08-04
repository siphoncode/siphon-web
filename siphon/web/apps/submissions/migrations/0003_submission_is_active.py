# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-18 08:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0002_auto_20160216_0828'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='is_active',
            field=models.BooleanField(default=False, help_text='Signals whether a submission is ready for clients to upgrade to.'),
        ),
    ]
