# Generated by Django 5.0.6 on 2024-06-25 19:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0018_groupmessage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='GroupMessage',
            new_name='TelegramMessage',
        ),
    ]