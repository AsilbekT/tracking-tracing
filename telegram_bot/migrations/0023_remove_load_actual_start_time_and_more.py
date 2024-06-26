# Generated by Django 5.0.6 on 2024-06-25 20:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0022_load_actual_start_time_alter_load_assigned_trailer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='load',
            name='actual_start_time',
        ),
        migrations.AlterField(
            model_name='load',
            name='assigned_driver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='laods', to='telegram_bot.driver'),
        ),
        migrations.AlterField(
            model_name='load',
            name='assigned_trailer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_trailer', to='telegram_bot.trailer'),
        ),
    ]
