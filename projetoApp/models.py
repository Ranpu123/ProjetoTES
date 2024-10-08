from django.db import models
from django.contrib.auth.models import AbstractUser
from localflavor.br.models import BRCPFField
from .managers import CustomUserManager, EventoManager, ProfessorManager, InscricaoManager, ParticipanteManager, AlunoManager
from datetime import date, datetime, time

# Create your models here.
class CustomUser(AbstractUser):
    first_name = models.CharField(max_length = 30, blank = True)
    last_name = models.CharField(max_length = 30, blank = True)
    username = models.CharField(max_length = 30, blank= True, unique=False, default="")
    email = models.EmailField(verbose_name="E-mail",unique=True)
    validated = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

class Usuario(models.Model):
    user = models.OneToOneField(CustomUser, on_delete = models.CASCADE, null=True)
    nome = models.CharField(verbose_name = "Nome", max_length = 50, blank = False)
    sobrenome = models.CharField(verbose_name = "Sobrenome", max_length = 50, blank = False)
    cpf = BRCPFField(name="CPF")

    def __str__(self):
        return self.user.email

class Participante(Usuario):
    objects = ParticipanteManager()
    def __str__(self):
        return f'{self.nome} {self.sobrenome}'

class Aluno(Usuario):
    objects = AlunoManager()
    def __str__(self):
        return f'{self.nome} {self.sobrenome}'

class Professor(Usuario):
    objects = ProfessorManager()

class Evento(models.Model):
    tema = models.CharField(verbose_name = "Tema", max_length = 255, blank = False)
    descricao = models.TextField(verbose_name = "Descrição", blank = False)
    data = models.DateField(verbose_name = "Data", null = False)
    horario_inicio = models.TimeField(verbose_name = "Horario Inicio", blank = True,default="8:00")
    horario_fim = models.TimeField(verbose_name= "Horario Fim", blank = True, default="18:00")
    logradouro = models.CharField(verbose_name= "Logradouro", max_length=255, blank=False, default="R. Pref. Brásílio Ribas, 775")
    bairro = models.CharField(verbose_name= "Bairro", max_length=255, blank=False, default="São José")
    cidade = models.CharField(verbose_name= "Cidade", max_length=50, blank=False, default="Ponta Grossa")
    estado = models.CharField(verbose_name= "UF", max_length=50, blank=False, default="Paraná")
    banner = models.URLField(verbose_name="Banner", blank = True)
    ativo = models.BooleanField(verbose_name="Ativo", blank=False, null= False, default=True)

    objects = EventoManager()

    def duracaoEvento(self):
        inicio = datetime.combine(date.today(), self.horario_fim)
        fim = datetime.combine(date.today(), self.horario_inicio)
        diff = inicio - fim
        return diff.total_seconds() / 3600

    def __str__(self):
        return self.tema

class Exibicao(models.Model):
    topico = models.CharField(verbose_name="Tópico", max_length = 255, blank=False)
    descricao = models.TextField(verbose_name="Descrição", blank=True)
    alunos = models.ManyToManyField(Aluno, verbose_name="Alunos")
    professores = models.ManyToManyField(Professor, verbose_name="Professores")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=True)
    ativo = models.BooleanField(verbose_name="Ativo", blank=False, null= False, default=True)
    data_cadastro = models.DateField(verbose_name="Data Criação", default=date.today)

class Avaliacao(models.Model):
    dataAvaliacao = models.DateField(verbose_name="Data Avaliação", null=False)
    descricao = models.TextField(verbose_name="Decrição", blank=False)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, null=False)
    exibicao = models.ForeignKey(Exibicao, on_delete=models.CASCADE, null=False)

class Convite(models.Model):
    emailDst = models.EmailField(verbose_name="Email")
    mensagem = models.TextField(verbose_name="Mensagem", blank=True)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=False)

class Inscricao(models.Model):
    dataHora = models.DateTimeField(verbose_name="Horario")
    confirmado = models.BooleanField()
    participante = models.ForeignKey(Participante, on_delete=models.CASCADE, null=False)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=True)

    objects = InscricaoManager()
    
class CheckIn(models.Model):
    dataHora = models.DateTimeField(verbose_name="Horario")
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE)

class Certificado(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    dataEmissao = models.DateField(verbose_name="Data Emissão", null = False)
    codigo = models.CharField(verbose_name="Código", max_length=255, blank=True)
    
