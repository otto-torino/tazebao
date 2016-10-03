# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-29 12:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0021_auto_20160929_1458'),
        ('mosaico', '0008_auto_20160220_1057'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='client',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='newsletter.Client', verbose_name='client'),
            preserve_default=False,
        ),
    ]
