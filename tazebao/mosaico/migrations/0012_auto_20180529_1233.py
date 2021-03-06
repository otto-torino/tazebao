# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-05-29 10:33
from __future__ import unicode_literals

from django.db import migrations, models
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mosaico', '0011_auto_20161018_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='image',
            field=sorl.thumbnail.fields.ImageField(upload_to='uploads', verbose_name='immagine'),
        ),
        migrations.AlterField(
            model_name='upload',
            name='name',
            field=models.CharField(max_length=200, verbose_name='nome'),
        ),
    ]
