# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-20 13:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0009_auto_20160229_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='platform',
            field=models.CharField(choices=[('ios', 'iOS'), ('android', 'Android')], max_length=20),
        ),
    ]