from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.http import Http404
from django.utils import timezone
from django.db.models import Value as V
from django.db.models.functions import Concat  
from django.db.models import Count  
import datetime

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    

class EventoManager(models.Manager):
    def get_home_event(self):
        dt = datetime.date.today()
        evento = self.filter(data__gte=dt, ativo=True).order_by('data').first()
        if not evento:
            evento = self.filter(data__lte=dt, ativo=True).order_by('data').first()
            if not evento:
                raise Http404("Event does not exist")
        return evento
    
    def get_last_event(self):
        dt = datetime.date.today()
        evento = self.filter(data__lte=dt, ativo=True).order_by('data').first()
        if not evento:
            raise Http404("Event does not exist")
        return evento
    
    def get_filtered_evento(self,filter):
        eventos = self.filter(tema__icontains=filter).order_by('data')
        return eventos

class ProfessorManager(models.Manager):
    def get_filtered_professor(self,filter):
        professores = self.annotate(full_name=Concat('nome', V(" "), 'sobrenome')).filter(full_name__icontains=filter).order_by('full_name')
        return professores
    
class InscricaoManager(models.Manager):
    def get_filtered_inscricao(self,filter,evento):
        inscricoes = self.annotate(full_name=Concat('participante__nome', V(" "), 'participante__sobrenome')).annotate(has_checkin=Count('checkin')).filter(full_name__icontains=filter).order_by('full_name')
        return inscricoes
    
class ParticipanteManager(models.Manager):
    def get_filtered_participante(self,filter):
        participante = self.annotate(full_name=Concat('nome', V(" "), 'sobrenome')).filter(full_name__icontains=filter).order_by('full_name')
        return participante 

class AlunoManager(models.Manager):
    def get_filtered_aluno(self,filter):
        aluno = self.annotate(full_name=Concat('nome', V(" "), 'sobrenome')).filter(full_name__icontains=filter).order_by('full_name')
        return aluno       