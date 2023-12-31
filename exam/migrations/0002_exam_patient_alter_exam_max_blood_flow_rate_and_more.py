# Generated by Django 4.2.7 on 2023-11-11 18:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0001_initial'),
        ('exam', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='patient.patient', verbose_name='Paciente'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='max_blood_flow_rate',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Taxa Máxima de Fluxo Sanguíneo'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='max_diameter',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Diâmetro Máximo'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='rest_diameter',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Diâmetro em Repouso'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='vasodilatation_rate',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Taxa de Vasodilatação'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='vessel_wall_thickness',
            field=models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Espessura da Parede Vascular'),
        ),
    ]
