from django.db import models
from django.utils import timezone
from django.contrib import admin
from menu.models import Partner

choice_gender = (
    ('M', 'Male'),
    ('F', 'Female'))

choice_blood = (
    ('A-', 'A-'),
    ('A+', 'A+'),
    ('AB-', 'AB-'),
    ('AB+', 'AB+'),
    ('B-', 'B-'),
    ('B+', 'B+'),
    ('O-', 'O-'),
    ('O+', 'O+'))

class Patient(models.Model):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, verbose_name='Parceiro')
    medical_record = models.CharField(max_length=20, verbose_name='Prontuário Médico')
    name = models.CharField(max_length=50, verbose_name='Nome')
    address = models.CharField(max_length=70, null=True, blank=True, verbose_name='Endereço')
    city = models.CharField(max_length=30, null=True, blank=True, verbose_name='Cidade')
    state = models.CharField(max_length=30, null=True, blank=True, verbose_name='Estado')
    country = models.CharField(max_length=30, null=True, blank=True, verbose_name='País')
    email = models.EmailField(max_length=50, null=True, blank=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefone')
    cellphone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Celular')
    birth_date = models.DateField(null=True, blank=True, default=timezone.now, verbose_name='Data de Nascimento')
    gender = models.CharField(max_length=1, null=True, blank=True, choices=choice_gender, verbose_name='Gênero')
    blood = models.CharField(max_length=3, null=True, blank=True, choices=choice_blood, verbose_name='Tipo Sanguíneo')
    weight = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2, verbose_name='Peso')
    height = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2, verbose_name='Altura')
    obs = models.CharField(max_length=140, null=True, blank=True, verbose_name='Observações')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

admin.site.register(Patient)