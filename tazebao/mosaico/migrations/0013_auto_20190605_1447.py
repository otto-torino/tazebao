# Generated by Django 2.2.2 on 2019-06-05 12:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mosaico', '0012_auto_20180529_1233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='template',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='newsletter.Client', verbose_name='client'),
        ),
    ]
