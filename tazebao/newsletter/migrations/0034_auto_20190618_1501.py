# Generated by Django 2.2.2 on 2019-06-18 13:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0033_failedemail'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscriber',
            options={'ordering': ('email',), 'verbose_name': 'Iscritto', 'verbose_name_plural': 'Iscritti'},
        ),
        migrations.RemoveField(
            model_name='failedemail',
            name='email',
        ),
        migrations.AddField(
            model_name='failedemail',
            name='subscriber',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='failedemails', to='newsletter.Subscriber', verbose_name='iscritto'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='failedemail',
            name='dispatch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='failedemails', to='newsletter.Dispatch', verbose_name='invio'),
        ),
    ]
