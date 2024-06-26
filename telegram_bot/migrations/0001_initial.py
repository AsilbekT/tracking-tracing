# Generated by Django 5.0.6 on 2024-06-21 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Trailer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('samsara_id', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('serial', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=50)),
                ('enabled_for_mobile', models.BooleanField(default=False)),
            ],
        ),
    ]
