# Generated by Django 4.2.7 on 2023-11-14 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0004_alter_exam_max_blood_flow_rate_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='video_file',
            field=models.FileField(upload_to='exam_videos/', verbose_name='Vídeo do Exame'),
        ),
    ]
