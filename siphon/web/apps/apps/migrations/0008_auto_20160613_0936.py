# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-06-13 09:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0007_app_beta_testing_alias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='app',
            name='beta_testing_alias',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='master_app', to='apps.App'),
        ),
    ]
