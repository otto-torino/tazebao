# Generated by Django 2.2.2 on 2020-01-03 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0038_auto_20191129_1035'),
    ]

    operations = [
        migrations.AddField(
            model_name='dispatch',
            name='test',
            field=models.BooleanField(default=False),
        ),
    ]