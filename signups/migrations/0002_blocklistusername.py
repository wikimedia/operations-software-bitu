# Generated by Django 3.2.12 on 2023-05-04 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockListUsername',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('regex', models.CharField(max_length=255)),
                ('comment', models.CharField(max_length=255)),
            ],
        ),
    ]
