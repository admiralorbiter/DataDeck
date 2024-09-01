# Generated by Django 5.0 on 2024-09-01 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_app', '0025_media_graph_tag_media_variable_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='is_graph',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='media',
            name='graph_tag',
            field=models.CharField(blank=True, choices=[('bar', 'Bar Chart'), ('line', 'Line Graph'), ('pie', 'Pie Chart')], max_length=50, null=True),
        ),
    ]