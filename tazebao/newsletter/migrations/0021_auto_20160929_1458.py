# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-29 12:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0020_auto_20160928_1001'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usercampaign',
            options={'verbose_name': 'Campagna', 'verbose_name_plural': 'Campagne'},
        ),
        migrations.AlterModelOptions(
            name='userclient',
            options={'verbose_name': 'Client', 'verbose_name_plural': 'Client'},
        ),
        migrations.AlterModelOptions(
            name='userdispatch',
            options={'verbose_name': 'Invio Campagna', 'verbose_name_plural': 'Invii Campagne'},
        ),
        migrations.AlterModelOptions(
            name='usermailermessage',
            options={'verbose_name': 'Log coda di invio', 'verbose_name_plural': 'Log code di invio'},
        ),
        migrations.AlterModelOptions(
            name='usersubscriber',
            options={'verbose_name': 'Iscritto', 'verbose_name_plural': 'Iscritti'},
        ),
        migrations.AlterModelOptions(
            name='usersubscriberlist',
            options={'verbose_name': 'Lista iscritti', 'verbose_name_plural': 'Liste iscritti'},
        ),
        migrations.AlterModelOptions(
            name='usertopic',
            options={'verbose_name': 'Topic', 'verbose_name_plural': 'Topic'},
        ),
        migrations.AlterModelOptions(
            name='usertracking',
            options={'verbose_name': 'Traking', 'verbose_name_plural': 'Tracking'},
        ),
        migrations.RemoveField(
            model_name='dispatch',
            name='sent_recipients',
        ),
    ]