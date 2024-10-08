# Generated by Django 3.2.12 on 2022-12-16 12:41

from django.db import migrations, models
import django.db.models.deletion
import ldapbackend.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Signup',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer.', max_length=150, unique=True, validators=[ldapbackend.validators.LDAPUsernameValidator, ldapbackend.validators.UnixUsernameRegExValidator()], verbose_name='username')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
            ],
        ),
        migrations.CreateModel(
            name='SignupPassword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(max_length=150)),
                ('value', models.CharField(max_length=256)),
                ('signup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='signups.signup')),
            ],
        ),
    ]
