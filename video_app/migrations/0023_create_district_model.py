from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('video_app', '0022_convert_module_3_to_2'),
    ]

    operations = [
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        # Add a temporary column for the district foreign key
        migrations.AddField(
            model_name='customadmin',
            name='district_new',
            field=models.ForeignKey('video_app.District', null=True, on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='observer',
            name='district_new',
            field=models.ForeignKey('video_app.District', null=True, on_delete=models.PROTECT),
        ),
    ] 