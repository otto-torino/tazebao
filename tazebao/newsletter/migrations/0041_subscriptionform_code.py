# Generated by Django 2.2.2 on 2023-03-01 12:47

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0040_auto_20230301_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionform',
            name='code',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
