# Generated by Django 3.2.12 on 2023-08-25 12:33

from django.db import migrations, models
import ldapbackend.validators


class Migration(migrations.Migration):

    dependencies = [
        ('signups', '0003_auto_20230511_0620'),
    ]

    operations = [
        migrations.AddField(
            model_name='signup',
            name='uid',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 32 characters or fewer.', max_length=32, null=True, unique=True, validators=[ldapbackend.validators.UnixUsernameRegExValidator()], verbose_name='UNIX shell username'),
        ),
        migrations.AlterField(
            model_name='signup',
            name='email',
            field=models.EmailField(max_length=254, unique=True, validators=[ldapbackend.validators.LDAPEmailValidator], verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='signup',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer.', max_length=150, unique=True, verbose_name='username'),
        ),
    ]
