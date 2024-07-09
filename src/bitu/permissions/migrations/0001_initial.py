# Generated by Django 3.2.12 on 2024-07-19 10:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('key', models.CharField(max_length=150)),
                ('system', models.CharField(max_length=150)),
                ('status', models.CharField(choices=[('AP', 'Approved'), ('CN', 'Cancelled'), ('PN', 'Pending'), ('SY', 'Synchronized'), ('RJ', 'Rejected')], default='PN', max_length=2)),
                ('comment', models.TextField(help_text='Please provide a reasoning for this request')),
                ('ticket', models.CharField(blank=True, default='', help_text='Phabricator ticket, if available.', max_length=256)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='permission_requests', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('comment', models.TextField()),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='permissions.permissionrequest')),
            ],
        ),
    ]
