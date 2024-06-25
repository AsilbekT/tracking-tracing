# Generated by Django 5.0.6 on 2024-06-21 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_delete_trailers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trailer',
            name='enabled_for_mobile',
        ),
        migrations.RemoveField(
            model_name='trailer',
            name='model',
        ),
        migrations.RemoveField(
            model_name='trailer',
            name='serial',
        ),
        migrations.AddField(
            model_name='trailer',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trailer',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]