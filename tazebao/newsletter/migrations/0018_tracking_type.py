# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-27 12:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0017_auto_20160926_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracking',
            name='type',
            field=models.IntegerField(choices=[(1, 'apertura'), (2, 'click')], default=1, verbose_name='tipo'),
            preserve_default=False,
        ),
    ]
