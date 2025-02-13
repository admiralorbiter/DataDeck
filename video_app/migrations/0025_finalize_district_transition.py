from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('video_app', '0024_convert_district_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customadmin',
            name='district',
        ),
        migrations.RemoveField(
            model_name='observer',
            name='district',
        ),
        migrations.RenameField(
            model_name='customadmin',
            old_name='district_new',
            new_name='district',
        ),
        migrations.RenameField(
            model_name='observer',
            old_name='district_new',
            new_name='district',
        ),
    ] 