import os
import uuid
from django.db import models
from django.contrib import admin
from menu.models import Partner

from patient.models import Patient

def get_upload_filename(instance, filename):
    name, ext = filename.split('.')
    filename = "%s.%s" % (name + '_' + str(uuid.uuid4()), ext)
    return os.path.join('exam_videos', filename)

class Exam(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, verbose_name='Paciente', null=True, blank=True)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, verbose_name='Parceiro', null=True)
    date = models.DateTimeField(verbose_name='Data e Hora', null=True, blank=True)
    vasodilatation_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Taxa de Vasodilatação',
        help_text="%"
    )
    rest_diameter = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Diâmetro em Repouso',
        help_text="mm"
    )
    max_diameter = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Diâmetro Máximo',
        help_text="mm"
    )
    max_blood_flow_rate = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='Taxa Máxima de Fluxo Sanguíneo'
    )
    vessel_wall_thickness = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Espessura da Parede Vascular',
        help_text="mm"
    )

    rest_graph = models.ImageField(
        upload_to='exam_images/', null=True, blank=True,
        verbose_name='Gráfico Rest'
    )
    after_cuff_released_graph = models.ImageField(
        upload_to='exam_images/', null=True, blank=True,
        verbose_name='Gráfico After Cuff Released'
    )
    video_file = models.FileField(
        upload_to=get_upload_filename, # dir = exam_videos/
        verbose_name='Vídeo do Exame'
    )
    processed_video_file = models.FileField(
        upload_to='processed_exam_videos/', null=True, blank=True,
        verbose_name='Vídeo processado do Exame'
    )
    segmentation_video_file = models.FileField(
        upload_to='segmentation_exam_videos/', null=True, blank=True,
        verbose_name='Vídeo segmentado do Exame'
    )
    processing_status = models.CharField(verbose_name='Status do processamento', default='queued', max_length=1024)

    def __str__(self):
        return f'Exame #{self.id}'

    class Meta:
        ordering = ['id']

admin.site.register(Exam)