# Generated by Django 2.2.2 on 2019-06-07 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0031_planning'),
    ]

    operations = [
        migrations.AddField(
            model_name='planning',
            name='sent',
            field=models.BooleanField(default=False, verbose_name='inviata'),
        ),
    ]
