# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-09 10:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0006_userdispatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='slug',
            field=models.SlugField(default='', verbose_name='slug'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='client',
            name='slug',
            field=models.SlugField(default='', verbose_name='slug'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='campaign',
            name='view_online',
            field=models.BooleanField(default=True, verbose_name='visualizza online'),
        ),
    ]
