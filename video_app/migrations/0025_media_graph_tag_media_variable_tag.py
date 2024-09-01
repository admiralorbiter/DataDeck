# Generated by Django 5.0 on 2024-09-01 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_app', '0024_rename_likes_media_graph_likes_media_eye_likes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='graph_tag',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='media',
            name='variable_tag',
            field=models.CharField(blank=True, choices=[('time', 'Time-based'), ('category', 'Categorical'), ('numeric', 'Numerical')], max_length=50, null=True),
        ),
    ]
