# Generated by Django 3.2.12 on 2024-07-31 11:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pyotp


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secret', models.CharField(default=pyotp.random_base32, max_length=32)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]