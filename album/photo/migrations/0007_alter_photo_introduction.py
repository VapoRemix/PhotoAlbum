# Generated by Django 4.2.10 on 2024-02-21 02:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0006_remove_photo_image_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='introduction',
            field=models.TextField(blank=True, default=1, max_length=500, verbose_name='img_story'),
            preserve_default=False,
        ),
    ]
