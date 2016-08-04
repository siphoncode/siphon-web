# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('streamers', '__first__'),
        ('bundlers', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='App',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('app_id', models.CharField(max_length=64, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BaseVersion',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=32)),
                ('latest', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='app',
            name='base_version',
            field=models.ForeignKey(to='apps.BaseVersion'),
        ),
        migrations.AddField(
            model_name='app',
            name='bundler',
            field=models.ForeignKey(related_name='apps', to='bundlers.Bundler'),
        ),
        migrations.AddField(
            model_name='app',
            name='streamer',
            field=models.ForeignKey(related_name='apps', to='streamers.Streamer'),
        ),
        migrations.AddField(
            model_name='app',
            name='user',
            field=models.ForeignKey(related_name='apps', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='app',
            unique_together=set([('user', 'name')]),
        ),
    ]
