"""
URL configuration for projetoTES project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from projetoApp import views

urlpatterns = [
    path('admin_evento/', views.adminEvento, name = "adminEvento"),
    path('admin_evento/cadastrar/', views.adminCadastrarEvento, name = "adminCadastrarEvento"),
    path('admin_evento/<int:pk>/', views.adminEditarEvento, name = "adminEditarEvento"),
    path('admin_professores/', views.adminProfessores, name = "adminProfessores"),
    path('admin_professores/cadastrar/', views.adminCadastrarProfessores, name = "adminCadastrarProfessores"),
    path('admin_professores/<int:pk>/', views.adminEditarProfessores, name = "adminEditarProfessores"),
    path('admin_checkin/', views.adminCheckin, name = "adminCheckin"),
    path('admin_checkin/<int:pk_evento>/<int:pk_inscricao>', views.adminCheckinValidar, name = "adminCheckinValidar"),
    path('admin_exibicao/', views.adminExibicao, name = "adminExibicao"),
    path('admin_exibicao/cadastrar', views.adminCadastrarExibicao, name = "adminCadastrarExibicao"),
    path('admin_exibicao/<int:pk>/', views.adminEditarExibicao, name = "adminEditarExibicao"),
    path('admin_exibicao_visualizar/<int:pk>/', views.adminVisualizarExibicao, name = "adminVisualizarExibicao"),
    path('admin_avaliar/<int:pk_aluno>/<int:pk_exibicao>', views.adminAvaliar, name = "adminAvaliar"),
    path('admin_avaliar/cadastrar/<int:pk_aluno>/<int:pk_exibicao>', views.adminCadastrarAvaliacao, name = "adminCadastrarAvaliacao"),
    path('admin_avaliar/<int:pk>', views.adminEditarAvaliacao, name = "adminEditarAvaliacao"),
    path('admin_participante/', views.adminParticipante, name = "adminParticipante"),
    path('admin_participante/cadastrar', views.adminCadastrarParticipante, name = "adminCadastrarParticipante"),
    path('admin_participante/<int:pk>', views.adminEditarParticipante, name = "adminEditarParticipante"),
    path('admin_aluno/', views.adminAluno, name = "adminAluno"),
    path('admin_aluno/cadastrar', views.adminCadastrarAluno, name = "adminCadastrarAluno"),
    path('admin_aluno/<int:pk>', views.adminEditarAluno, name = "adminEditarAluno"),
    path('admin_certificados/', views.adminCertificado, name = "adminCertificado"),
    path('certificados/', views.certificados, name = "certificados"),
    path("", views.index, name = 'home'),
    path("login/", views.entrar, name = 'login'),
    path("registrar/", views.registrarUsuario, name = 'registrarUsuario'),
    path("registrar_professor/", views.registrarProfessor, name = 'registrarProfessor'),
    path("logout/", views.sair, name = 'logout'),
    path('inscrever/<int:event_id>/', views.inscrever, name='inscrever'),
    path('desinscrever/<int:event_id>/', views.desinscrever, name='desinscrever'),
    path('admin_download_certificado/<int:pk_evento>/<int:pk_participante>/', views.adminDownloadCertificado, name='adminDownloadCertificado'),
    path('download_certificado/<int:pk_evento>/<int:pk_participante>/', views.downloadCertificado, name='downloadCertificado'),

]
