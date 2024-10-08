# Generated by Django 3.2.12 on 2024-08-05 10:01

import accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_securitytoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecoveryCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(default=accounts.models.generate_recovery_key, max_length=16)),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.securitytoken')),
            ],
        ),
    ]
