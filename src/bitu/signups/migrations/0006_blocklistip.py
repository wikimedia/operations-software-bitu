# Generated by Django 3.2.12 on 2024-04-08 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signups', '0005_auto_20240405_0836_squashed_0006_alter_uservalidation_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockListIP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('expiry', models.DateTimeField(auto_now_add=True)),
                ('origin', models.CharField(default='manual', max_length=255)),
                ('start', models.GenericIPAddressField()),
                ('end', models.GenericIPAddressField()),
                ('comment', models.CharField(max_length=255)),
            ],
        ),
    ]
