# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-11 03:04
from __future__ import unicode_literals

from django.db import migrations
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mosaico', '0002_auto_20160211_0301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='image',
            field=sorl.thumbnail.fields.ImageField(upload_to='uploads'),
        ),
    ]
