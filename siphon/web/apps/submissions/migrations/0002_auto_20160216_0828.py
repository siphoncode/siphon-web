# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-16 08:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='platform',
            field=models.CharField(choices=[('ios', 'iOS')], default='ios', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='platform_password',
            field=models.CharField(default='dummy', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='platform_username',
            field=models.CharField(default='dummy', max_length=255),
            preserve_default=False,
        ),
    ]
