# Generated by Django 2.2.2 on 2023-03-01 12:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0041_subscriptionform_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriptionform',
            name='slug',
        ),
    ]
