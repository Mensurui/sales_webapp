# Generated by Django 5.0.2 on 2024-02-15 09:03

import django.contrib.auth.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('origin', '0010_productinterest_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserWithCompanyCount',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
