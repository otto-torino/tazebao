# Generated by Django 2.2.2 on 2023-07-27 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0054_systemmessage_systemmessageread'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemmessage',
            name='title',
            field=models.CharField(default='', max_length=255, verbose_name='titolo'),
            preserve_default=False,
        ),
    ]
