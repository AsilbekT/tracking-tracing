# Generated by Django 5.0.6 on 2024-06-25 19:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0016_alter_load_assigned_driver'),
    ]

    operations = [
        migrations.AddField(
            model_name='load',
            name='assigned_broker',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_broker', to='telegram_bot.trailer'),
        ),
        migrations.AlterField(
            model_name='load',
            name='assigned_trailer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_trailer', to='telegram_bot.trailer'),
        ),
    ]
