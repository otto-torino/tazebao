# Generated by Django 2.2.2 on 2023-07-27 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0047_suggestionrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriber',
            name='suggestions_per_day',
            field=models.IntegerField(default=3, verbose_name='suggerimenti giornalieri'),
        ),
    ]
