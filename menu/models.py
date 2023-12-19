from django import forms
from django.db import models
from django.contrib.auth.models import Group, AbstractUser, UserManager
from django.contrib import admin

    
class PartnerManager(UserManager):
    def create_user(self, username, email, contact, password=None):
        if not email or not contact:
            raise ValueError('Users must have an email address and a contact')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            contact=contact
        )

        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_superuser(self, username, email, contact, password):
        user = self.create_user(
            email=email,
            username=username,
            password=password,
            contact=contact
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class Partner(AbstractUser):
    contact = models.CharField(max_length=50, verbose_name='Contato', default='')
    address = models.CharField(max_length=70, null=True, blank=True, verbose_name='Endereço')
    city = models.CharField(max_length=30, null=True, blank=True, verbose_name='Cidade')
    state = models.CharField(max_length=30, null=True, blank=True, verbose_name='Estado')
    country = models.CharField(max_length=30, null=True, blank=True, verbose_name='País')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Telefone')
    cellphone = models.CharField(max_length=20, null=True, blank=True, verbose_name='Celular')
    website = models.URLField(max_length=70, null=True, blank=True, verbose_name='Site')
    # image = models.ImageField(upload_to='partner_images/', null=True, blank=True, verbose_name='Imagem')

    objects = PartnerManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['contact', 'email']

    def __str__(self):
        if not self.first_name:
            return self.username
        
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ['username']