# Generated by Django 4.2.7 on 2023-11-11 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_alter_partner_options_remove_partner_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='partner',
            options={'ordering': ['username']},
        ),
    ]