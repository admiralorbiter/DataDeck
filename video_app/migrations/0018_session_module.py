# Generated by Django 5.1.1 on 2024-12-15 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_app', '0017_alter_media_variable_tag_observer'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='module',
            field=models.CharField(choices=[('general', 'Final Project'), ('3', 'Module 3')], default='3', max_length=20),
        ),
    ]
