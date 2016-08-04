# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('streamers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streamer',
            name='port',
            field=models.IntegerField(default=443),
        ),
    ]
