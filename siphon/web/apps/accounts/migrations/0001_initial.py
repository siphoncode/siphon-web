# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('code', models.CharField(unique=True, max_length=255)),
                ('user', models.OneToOneField(null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(serialize=False, primary_key=True, max_length=64)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(related_name='auth_token', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
