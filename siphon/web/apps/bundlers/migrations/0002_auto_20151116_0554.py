# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bundlers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bundler',
            name='port',
            field=models.IntegerField(default=443),
        ),
    ]
