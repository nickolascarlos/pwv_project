# Generated by Django 4.2.7 on 2023-11-14 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0006_exam_partner'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='processed_video_file',
            field=models.FileField(blank=True, null=True, upload_to='processed_exam_videos/', verbose_name='Vídeo processado do Exame'),
        ),
    ]