# Generated by Django 5.0.6 on 2024-06-24 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0009_load'),
    ]

    operations = [
        migrations.AddField(
            model_name='load',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('finished', 'Finished')], default='pending', max_length=20),
        ),
    ]
