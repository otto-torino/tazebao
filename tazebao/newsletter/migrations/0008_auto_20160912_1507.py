# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-12 13:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0007_auto_20160909_1244'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subscriber',
            unique_together=set([('client', 'email')]),
        ),
    ]
