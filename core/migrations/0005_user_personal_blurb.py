# Generated by Django 5.1.1 on 2024-10-27 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_user_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='personal_blurb',
            field=models.TextField(blank=True, null=True),
        ),
    ]
