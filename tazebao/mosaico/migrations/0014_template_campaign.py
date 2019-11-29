# Generated by Django 2.2.2 on 2019-11-26 13:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0036_auto_20191018_1543'),
        ('mosaico', '0013_auto_20190605_1447'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to='newsletter.Campaign', verbose_name='campagna'),
        ),
    ]
