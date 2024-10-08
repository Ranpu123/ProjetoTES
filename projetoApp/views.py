from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db.models import Count 
from datetime import date, datetime, time
from .forms import CustomUserForm, ParticipanteForm, EventoForm, ProfessorForm, ExibicaoForm, AddAlunoExibicaoForm, AddProfessorExibicaoForm, AlunoForm, AvaliacaoForm
from .models import *
from .certificate import generateCertificado

def index(request):
    context = {}
    context['current_date'] = date.today()
    context['evento'] = evento = Evento.objects.get_home_event()
    context["exibicoes"] = Exibicao.objects.filter(evento=evento).order_by("topico")

    if request.user.is_authenticated:   
        context['user_is_participante'] = Participante.objects.filter(user=request.user).exists()
        context['user_is_inscrito'] = Inscricao.objects.filter(evento=evento, participante__user=request.user).exists()
    else:
        context['user_is_participante'] = False
        context['user_is_inscrito'] = False

    return render(request, "home.html",context)

@login_required(login_url="/login")
def inscrever(request, event_id):
    evento = get_object_or_404(Evento, pk=event_id)
    participante = Participante.objects.filter(user=request.user).first()
    
    context = {}
    context['user_is_participante'] = Participante.objects.filter(user=request.user).exists()
    context['user_is_inscrito'] = Inscricao.objects.filter(evento=evento, participante__user=request.user).exists()

    if not context['user_is_inscrito'] and context['user_is_participante']:
        inscricao = Inscricao.objects.create(evento=evento, participante=participante, confirmado=True,dataHora=datetime.now())
        inscricao.save()
        
    return redirect("home")

@login_required(login_url="/login")
def desinscrever(request, event_id):
    evento = get_object_or_404(Evento, pk=event_id)
    participante = Participante.objects.filter(user=request.user).first()
    
    context = {}
    context['user_is_participante'] = Participante.objects.filter(user=request.user).exists()
    context['user_is_inscrito'] = Inscricao.objects.filter(evento=evento, participante__user=request.user).exists()

    if context['user_is_inscrito'] and context['user_is_participante']:
        Inscricao.objects.filter(evento=evento, participante=participante).delete()

    return redirect("home")

def entrar(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('adminEvento')
        else:
            return redirect('home')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],password=form.cleaned_data['password'],)
            if user is not None:
                login(request, user)
                #messages.success(request, f"Olá, <b>{user.first_name}</b>! Você logou com sucesso!")
                print("LOGGED IN")
                if user.is_staff:
                    return redirect('adminEvento')
                else:
                    return redirect('home')
        else:
            for error in list(form.errors.values()):
                print(request, error) 
    
    form = AuthenticationForm()

    return render(request, 'login_user.html', context={'form':form})

def registrarUsuario(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = CustomUserForm(request.POST)
    form2 = ParticipanteForm(request.POST)
    if request.method == "POST":
        if form.is_valid() and form2.is_valid():
            user = form.save(commit=False)
            participante = form2.save(commit=False)

            user.first_name = form2.cleaned_data['nome']
            user.last_name = form2.cleaned_data['sobrenome']
            
            user.save()
            
            participante.user = user
            participante.save()
            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('home')
    else:
        form = CustomUserForm(request.POST)
        form2 = ParticipanteForm(request.POST)

    return render(request, 'registro.html', {'form': form, "form2":form2})

@login_required(login_url='login')
def sair(request):
    logout(request)
    #messages.info(request,"Deslogado com sucesso!")
    return redirect('home')

@login_required(login_url="login")
def adminEvento(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    eventos = Evento.objects.filter(ativo=True).order_by('data')
    context['eventos'] = eventos
    if 'filter' in request.GET:
        context['eventos'] = Evento.objects.get_filtered_evento(request.GET['filter'])
        return render(request, 'admin_evento.html', context)
    
    if 'pk_evento' in request.POST:
        print(Evento.objects.filter(pk=request.POST['pk_evento']))
        evento = Evento.objects.filter(pk=request.POST['pk_evento']).first()
        evento.ativo = False
        evento.save()
        return redirect('adminEvento')

    return render(request, 'admin_evento.html', context)

@login_required(login_url='login')
def adminCadastrarEvento(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    form = EventoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            evento = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminEvento')
        else:
            for error in list(form.errors.values()):
                pass
            context['form'] = EventoForm(request.POST)
    else:
        context['form'] = EventoForm(initial=EventoForm.get_inital_data())    

    return render(request, 'admin_evento_cadastrar.html', context)

@login_required(login_url='login')
def adminEditarEvento(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    evento = get_object_or_404(Evento,pk=pk)
    form = EventoForm(request.POST, instance=evento)
    if request.method == "POST":
        if form.is_valid():
            evento = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminEvento')
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = EventoForm(instance=evento)    

    return render(request, 'admin_evento_editar.html', context)


@login_required(login_url="login")
def adminProfessores(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    professores = Professor.objects.all().order_by('id')
    context['professores'] = professores
    if 'filter' in request.GET:
        context['professores'] = Professor.objects.get_filtered_professor(request.GET['filter'])
        return render(request, 'admin_professores.html', context)
    
    if 'pk_professor' in request.POST:
        professor = Professor.objects.filter(pk=request.POST['pk_professor']).first()
        professor.user.delete()
        professor.delete()
        return redirect('adminProfessores')
    
    if 'validar' in request.POST:
        professor = Professor.objects.filter(pk=request.POST['validar']).first()
        professor.user.validated = True
        professor.user.is_staff = True
        professor.user.save()
        return redirect('adminProfessores')

    
    return render(request, 'admin_professores.html', context)

@login_required(login_url='login')
def adminCadastrarProfessores(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    form = CustomUserForm(request.POST)
    form2 = ProfessorForm(request.POST)
    if request.method == "POST":
        if form.is_valid() and form2.is_valid():
            user = form.save(commit=False)
            participante = form2.save(commit=False)

            user.first_name = form2.cleaned_data['nome']
            user.last_name = form2.cleaned_data['sobrenome']
            user.validated = True
            user.is_staff = True
            
            user.save()
            
            participante.user = user
            participante.save()
            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('adminProfessores')
    else:
        form = CustomUserForm()
        form2 = ProfessorForm()
    
    context = {"form": form, "form2":form2}
    return render(request, 'admin_professores_cadastrar.html', context)

@login_required(login_url='login')
def adminEditarProfessores(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    professor = get_object_or_404(Professor,pk=pk)
    form = CustomUserForm(request.POST, instance=professor.user)
    form2 = ProfessorForm(request.POST, instance=professor)
    if request.method == "POST":
        if form2.is_valid() and form.is_valid():
            professor = form2.save()
            user = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminProfessores')
        else:
            for error in list(form2.errors.values()):
                pass

    context['form2'] = ProfessorForm(instance=professor)    
    context['form'] = CustomUserForm(instance=professor.user)

    return render(request, 'admin_professores_editar.html', context)

def registrarProfessor(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = CustomUserForm(request.POST)
    form2 = ProfessorForm(request.POST)
    if request.method == "POST":
        if form.is_valid() and form2.is_valid():
            user = form.save(commit=False)
            participante = form2.save(commit=False)

            user.first_name = form2.cleaned_data['nome']
            user.last_name = form2.cleaned_data['sobrenome']
            user.validated = False
            user.is_staff = True
            user.save()
            
            participante.user = user
            participante.save()
            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('home')
    else:
        form = CustomUserForm(request.POST)
        form2 = ProfessorForm(request.POST)

    return render(request, 'registro_professor.html', {'form': form, "form2":form2})

@login_required(login_url="/login")
def adminCheckin(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    context["evento"] = evento = Evento.objects.get_home_event()
    context["current_date"] = date.today()
    context["inscricoes"] = Inscricao.objects.filter(evento = evento).annotate(has_checkin=Count('checkin')).order_by("id")
    
    if 'filter' in request.GET:
        context['inscricoes'] = Inscricao.objects.get_filtered_inscricao(request.GET['filter'], evento)
        return render(request, "admin_checkin.html", context)
    
    return render(request, "admin_checkin.html", context)

@login_required(login_url="/login")
def adminCheckinValidar(request,pk_evento, pk_inscricao):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    evento = Evento.objects.get(pk=pk_evento)
    inscricao = get_object_or_404(Inscricao, pk=pk_inscricao, evento=evento)
    if not CheckIn.objects.filter(inscricao=inscricao).exists():
        checkin = CheckIn.objects.create(inscricao=inscricao, dataHora=datetime.now())
        checkin.save()

    return redirect('adminCheckin')

@login_required(login_url="/login")    
def adminExibicao(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    professor = Professor.objects.filter(user = request.user).first()
    context = {}
    context["eventos"] = eventos = Evento.objects.filter(ativo=1)
    context["exibicoes"] = Exibicao.objects.filter(professores__in=[professor])

    if 'filter' in request.GET:
        if request.GET['event'] == "-1":
            if request.GET['filter_by'] == "id":
                context["exibicoes"] = Exibicao.objects.filter(professores__in=[professor], topico__icontains=request.GET["filter"])
            elif request.GET["filter_by"] == "all":
                context["exibicoes"] = Exibicao.objects.filter(topico__icontains=request.GET["filter"])
            else:
                return redirect(adminExibicao)
        else:
            if request.GET['filter_by'] == "id":
                context["exibicoes"] = Exibicao.objects.filter(evento__pk=request.GET['event'], professores__in=[professor], topico__icontains=request.GET["filter"])
            elif request.GET["filter_by"] == "all":
                context["exibicoes"] = Exibicao.objects.filter(evento__pk=request.GET['event'], topico__icontains=request.GET["filter"])
            else:
                return redirect(adminExibicao)
        return render(request, "admin_exibicao.html", context)

    if 'pk_exibicao' in request.POST:
        exibicao = Exibicao.objects.filter(pk=request.POST['pk_exibicao']).first()
        exibicao.delete()
        return redirect(adminExibicao)

    return render(request, "admin_exibicao.html", context)

@login_required(login_url="/login")    
def adminCadastrarExibicao(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    form = ExibicaoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            exibicao = form.save()
            professor = Professor.objects.get(user = request.user)
            exibicao.professores.add(professor)
            exibicao.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminExibicao')
        else:
            for error in list(form.errors.values()):
                pass
            context['form'] = ExibicaoForm(request.POST)
    else:
        context['form'] = ExibicaoForm()
    return render(request, "admin_cadastrar_exibicao.html", context)

@login_required(login_url="/login")
def adminVisualizarExibicao(request,pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    context["exibicao"] = exibicao = Exibicao.objects.get(pk=pk)
    professor = Professor.objects.filter(user = request.user).first()
    form = AddAlunoExibicaoForm(request.POST)
    form2 = AddProfessorExibicaoForm(request.POST)
    
    if "pk_professor_remover" in request.POST:
        professor = Professor.objects.get(pk=request.POST["pk_professor_remover"])
        exibicao.professores.remove(professor)

    if "pk_aluno_remover" in request.POST:
        aluno = Aluno.objects.get(pk=request.POST["pk_aluno_remover"])
        exibicao.alunos.remove(aluno)
    
    if request.method == 'POST':
        if form2.is_valid():
            professor = form2.cleaned_data['professor']
            exibicao.professores.add(professor)

            return redirect("adminVisualizarExibicao", pk=pk)

        if form.is_valid():
            aluno = form.cleaned_data['aluno']
            exibicao.alunos.add(aluno)

            return redirect("adminVisualizarExibicao", pk=pk)
    else:
        form = AddAlunoExibicaoForm()
        form2 = AddProfessorExibicaoForm()
    
    context["form"] = form
    context["form2"] = form2
    context["size"] = exibicao.professores.count()
    context["in_exibicao"] = Exibicao.objects.filter(pk=pk,professores__in=[professor]).exists()
    return render(request, "admin_exibicao_visualizar.html", context)

@login_required(login_url='login')
def adminEditarExibicao(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    exibicao = get_object_or_404(Exibicao,pk=pk)
    form = ExibicaoForm(request.POST, instance=exibicao)
    
    if request.method == "POST":
        if form.is_valid():
            exibicao = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminExibicao')
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = ExibicaoForm(instance=exibicao)

    return render(request, 'admin_exibicao_editar.html', context)


@login_required(login_url="/login")
def adminParticipante(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    participante = Participante.objects.all().order_by('id')
    context['participantes'] = participante
    if 'filter' in request.GET:
        context['participantes'] = Participante.objects.get_filtered_participante(request.GET['filter'])
        return render(request, 'admin_participante.html', context)
    
    if 'pk_participante' in request.POST:
        participante = Participante.objects.filter(pk=request.POST['pk_participante']).first()
        participante.user.delete()
        participante.delete()
        return redirect('adminParticipante')
    
    return render(request, 'admin_participante.html', context)

@login_required(login_url='login')
def adminCadastrarParticipante(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    form = CustomUserForm(request.POST)
    form2 = ParticipanteForm(request.POST)
    if request.method == "POST":
        if form.is_valid() and form2.is_valid():
            user = form.save(commit=False)
            participante = form2.save(commit=False)

            user.first_name = form2.cleaned_data['nome']
            user.last_name = form2.cleaned_data['sobrenome']
            user.validated = False
            user.is_staff = False
            
            user.save()
            
            participante.user = user
            participante.save()
            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('adminParticipante')
    else:
        form = CustomUserForm()
        form2 = ParticipanteForm()
    
    context = {"form": form, "form2":form2}
    return render(request, 'admin_participante_cadastrar.html', context)

@login_required(login_url='login')
def adminEditarParticipante(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    participante = get_object_or_404(Participante,pk=pk)
    form = CustomUserForm(request.POST, instance=participante.user)
    form2 = ParticipanteForm(request.POST, instance=participante)
    if request.method == "POST":
        if form2.is_valid() and form.is_valid():
            participante = form2.save()
            user = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminParticipante')
        else:
            for error in list(form2.errors.values()):
                pass

    context['form2'] = ParticipanteForm(instance=participante)    
    context['form'] = CustomUserForm(instance=participante.user)

    return render(request, 'admin_participante_editar.html', context)

@login_required(login_url="/login")
def adminAluno(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    aluno = Aluno.objects.all().order_by('id')
    context['alunos'] = aluno
    
    if 'filter' in request.GET:
        context['alunos'] = Aluno.objects.get_filtered_aluno(request.GET['filter'])
        return render(request, 'admin_aluno.html', context)
    
    if 'pk_aluno' in request.POST:
        aluno = Aluno.objects.filter(pk=request.POST['pk_aluno']).first()
        aluno.delete()
        return redirect('adminAluno')
    
    return render(request, 'admin_aluno.html', context)

@login_required(login_url='/login')
def adminCadastrarAluno(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    form = AlunoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('adminAluno')
    else:
        form = AlunoForm()
    
    context = {"form": form}
    return render(request, 'admin_aluno_cadastrar.html', context)

@login_required(login_url='login')
def adminEditarAluno(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    aluno = get_object_or_404(Aluno,pk=pk)
    form = AlunoForm(request.POST, instance=aluno)
    if request.method == "POST":
        if form.is_valid():
            aluno = form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminAluno')
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = AlunoForm(instance=aluno)

    return render(request, 'admin_aluno_editar.html', context)


@login_required(login_url="/login")
def adminAvaliar(request, pk_exibicao, pk_aluno):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    context["aluno"]= aluno = get_object_or_404(Aluno,pk=pk_aluno)
    context["exibicao"] = exibicao = get_object_or_404(Exibicao,pk=pk_exibicao)
    avaliacao = Avaliacao.objects.filter(aluno=aluno, exibicao=exibicao)
    context['avaliacoes'] = avaliacao
    
    if 'filter' in request.GET:
        if request.GET["filter"] == "":
            return render(request, 'admin_avaliar_aluno.html', context)

        context['avaliacoes'] = Avaliacao.objects.filter(aluno=aluno, exibicao=exibicao, dataAvaliacao=request.GET['filter'])
        return render(request, 'admin_avaliar_aluno.html', context)
    
    if 'pk_avaliacao' in request.POST:
        avaliacao = Avaliacao.objects.filter(pk=request.POST['pk_avaliacao']).first()
        avaliacao.delete()
        return redirect('adminAvaliar', pk_exibicao=pk_exibicao, pk_aluno=pk_aluno)
    
    return render(request, 'admin_avaliar_aluno.html', context)

@login_required(login_url='/login')
def adminCadastrarAvaliacao(request, pk_aluno, pk_exibicao):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    form = AvaliacaoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            user = get_object_or_404(Aluno,pk=pk_aluno)
            exibicao = get_object_or_404(Exibicao,pk=pk_exibicao)
            avaliacao = form.save(commit=False)
            avaliacao.dataAvaliacao = date.today()
            avaliacao.aluno = user
            avaliacao.exibicao = exibicao
            avaliacao.save()

            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('adminAvaliar', pk_aluno, pk_exibicao)
    else:
        form = AvaliacaoForm()
    
    context = {"form": form}
    return render(request, 'admin_avaliar_aluno_cadastrar.html', context)

@login_required(login_url='login')
def adminEditarAvaliacao(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    avaliacao = get_object_or_404(Avaliacao,pk=pk)
    form = AvaliacaoForm(request.POST, instance=avaliacao)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            #messages.success(request, f"Evento Cadastrado com sucesso!")
            return redirect('adminAvaliar', pk_exibicao = avaliacao.exibicao.id, pk_aluno = avaliacao.aluno.id)
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = AvaliacaoForm(instance=avaliacao)
    return render(request, 'admin_avaliar_aluno_editar.html', context)

@login_required(login_url="/login")
def adminCertificado(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    context = {}
    context["evento"] = evento = Evento.objects.get_last_event()
    context["alunos"] = Aluno.objects.filter(exibicao__evento=evento).distinct()
    context["professores"] = Professor.objects.filter(exibicao__evento=evento).distinct()
    context["eventos"] = Evento.objects.filter(ativo=1, data__lte=date.today())

    if 'filter' in request.GET:
        if request.GET['event'] == "-1":
            context["alunos"] = Aluno.objects.get_filtered_aluno(request.GET['filter']).filter(exibicao__evento=evento)
            context["professores"] = Professor.objects.get_filtered_professor(request.GET['filter']).filter(exibicao__evento=evento)
        else:
            context["alunos"] = Aluno.objects.get_filtered_aluno(request.GET['filter']).filter(exibicao__evento=request.GET['event'])
            context["professores"] = Professor.objects.get_filtered_professor(request.GET['filter']).filter(exibicao__evento=request.GET['event'])
        return render(request, "admin_certificados.html", context)
    
    return render(request, "admin_certificados.html", context)

@login_required(login_url="/login")
def adminDownloadCertificado(request, pk_evento, pk_participante):

    evento = get_object_or_404(Evento, pk=pk_evento)
    usuario = get_object_or_404(Usuario, pk=pk_participante)
    certificado = Certificado.objects.filter(evento=evento, usuario=usuario)

    if(Exibicao.objects.filter(alunos=usuario, evento=evento).exists()):
        exibicao = Exibicao.objects.filter(alunos=usuario, evento=evento).first()
    elif(Exibicao.objects.filter(professores=usuario, evento=evento).exists()):
        exibicao = Exibicao.objects.filter(professores=usuario, evento=evento).first()
    else:
        redirect("adminCertificado")

    if certificado:
        pdf_path = certificado.first().codigo
    else:
        date_time = evento.data.strftime("%d/%m/%Y")
        diff = evento.data - exibicao.data_cadastro
        semana = (diff.days // 7) * 14
        pdf_path = generateCertificado(usuario.nome+" "+usuario.sobrenome, evento.tema, date_time, str(semana))
        certificado = Certificado(dataEmissao=datetime.now(), codigo=pdf_path, evento=evento, usuario=usuario)
        certificado.save()

    with open(pdf_path, "rb") as pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="certificado.pdf"'
    return response

@login_required(login_url="/login")
def certificados(request):
    context = {}
    context["participante"] = participante = Participante.objects.get(user=request.user.id)
    context["eventos"] = evento = Evento.objects.filter(inscricao__participante=participante, inscricao__checkin__isnull=False, data__lt=date.today()).distinct()
    print(evento)
    

    return render(request, "certificados.html", context)

@login_required(login_url="/login")
def downloadCertificado(request, pk_evento, pk_participante):
    evento = get_object_or_404(Evento, pk=pk_evento)
    participante = get_object_or_404(Participante, user=pk_participante)
    certificado = Certificado.objects.filter(evento=evento, usuario=participante)
    inscricao = Inscricao.objects.filter(evento = evento, participante = participante).first()
    check = CheckIn.objects.filter( inscricao = inscricao).first()

    if certificado:
        pdf_path = certificado.first().codigo
    else:
        if check:
            date_time = evento.data.strftime("%d/%m/%Y")
            pdf_path = generateCertificado(participante.nome+" "+participante.sobrenome, evento.tema, date_time, str(evento.duracaoEvento()))
            certificado = Certificado(dataEmissao=datetime.now(), codigo=pdf_path, evento=evento, usuario=participante)
            certificado.save()
        else:
            return redirect("certificados")
        
    with open(pdf_path, "rb") as pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="certificado.pdf"'
    return response