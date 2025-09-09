from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.db.models import OuterRef, Subquery, Q
from datetime import date, datetime
from django.http import HttpResponse
from django.contrib import messages
from .handlers import *
from .strategies import *
from .forms import *
from .models import *
from .certificate import generateCertificado
from .handlers import ParticipanteCheckInHandler, AlunoCheckInHandler

# Dicionário de estratégias
STRATEGIES = {
    'aluno': AlunoDeleteStrategy(),
    'professor': ProfessorDeleteStrategy(),
    'participante': ParticipanteDeleteStrategy(),
    'atividade': AtividadeDeleteStrategy(),
    'evento': EventoDeleteStrategy()
}

def index(request):
    context = {}
    context['current_date'] = date.today()
    context['evento'] = evento = Evento.objects.get_home_event()
    
    if evento is None:
        # Não há eventos disponíveis
        return render(request, "evento_indisponivel.html")
    
    context["atividades"] = Atividade.objects.filter(evento=evento).order_by("topico")
    
    if request.user.is_authenticated:   
        context['user_is_participante'] = Participante.objects.filter(user=request.user).exists()
        context['user_is_inscrito'] = Inscricao.objects.filter(evento=evento, participante__user=request.user).exists()
    else:
        context['user_is_participante'] = False
        context['user_is_inscrito'] = False

    return render(request, "home.html", context)

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
    if request.method == 'POST':
        user_form = CustomUserForm(request.POST)
        participante_form = ParticipanteForm(request.POST)
        
        if user_form.is_valid() and participante_form.is_valid():
            # Salva o usuário
            user = user_form.save()

            # Salva o participante vinculado ao usuário
            participante = participante_form.save(commit=False)
            participante.usuario = user  # Vincula o participante ao usuário
            participante.save()

            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect('home')  # Redireciona para a página inicial
    else:
        user_form = CustomUserForm()
        participante_form = ParticipanteForm()

    context = {
        'form': user_form,
        'form2': participante_form
    }

    return render(request, 'registro.html', context)

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
    eventos = Evento.objects.all().order_by('data')
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
            #messages.success(request, f"Evento Cadastrada com sucesso!")
            return redirect('adminEvento')
        else:
            for error in list(form.errors.values()):
                pass
            context['form'] = EventoForm(request.POST)
    else:
        context['form'] = EventoForm()    

    return render(request, 'admin_evento_cadastrar.html', context)

@login_required(login_url="login")
def adminEditarEvento(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            # Salva o evento
            evento = form.save()

            # Atualiza os horários das atividades
            for atividade in evento.atividade_set.all():
                horario_inicio = request.POST.get(f'horario_inicio_{atividade.id}')
                horario_fim = request.POST.get(f'horario_fim_{atividade.id}')
                capacidade_maxima = request.POST.get(f'capacidade_maxima_{atividade.id}')
                
                if horario_inicio and horario_fim and capacidade_maxima:
                    atividade.horario_inicio = horario_inicio
                    atividade.horario_fim = horario_fim
                    atividade.capacidade_maxima = capacidade_maxima
                    atividade.save()

            messages.success(request, "Evento e atividades atualizados com sucesso!")
            return redirect('adminEvento')
    else:
        form = EventoForm(instance=evento)

    context = {
        'form': form,
        'evento': evento,
    }
    return render(request, 'admin_evento_editar.html', context)

@login_required(login_url="/login")
def adminDesativarEvento(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')

    evento = get_object_or_404(Evento, id=pk)
    evento.ativo = False  # Desativa o evento
    evento.save()

    messages.success(request, f"Evento '{evento.tema}' desativado com sucesso.")
    return redirect('adminEvento')

@login_required(login_url="/login")
def adminReativarEvento(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')

    evento = get_object_or_404(Evento, id=pk)
    evento.ativo = True  # Reativa o evento
    evento.save()

    messages.success(request, f"Evento '{evento.tema}' reativado com sucesso.")
    return redirect('adminEvento')

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
            #messages.success(request, f"Atividade Cadastrado com sucesso!")
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
    # Obtendo o evento atual
    try:
        context["evento"] = evento = Evento.objects.get_last_event()
        context["current_date"] = date.today()

        # Lista de inscrições para o evento
        inscricoes = Inscricao.objects.filter(evento=evento)
        
        # Verificar se cada inscrição já possui check-in
        inscricoes_com_checkin = []
        for inscricao in inscricoes:
            has_checkin = CheckIn.objects.filter(inscricao=inscricao).exists()
            inscricoes_com_checkin.append({
                'inscricao': inscricao,
                'has_checkin': has_checkin
            })
        context["inscricoes_com_checkin"] = inscricoes_com_checkin

        # Lista de atividades do evento
        atividades_do_evento = Atividade.objects.filter(evento=evento)
        context["atividades"] = atividades_do_evento

        # Agrupar alunos por atividade
        alunos_por_atividade = []
        for atividade in atividades_do_evento:
            alunos_vinculados = atividade.alunos.all()  # Usando o related_name da relação ManyToMany
            alunos_com_checkin = []
            for aluno in alunos_vinculados:
                has_checkin = CheckIn.objects.filter(aluno=aluno, atividade=atividade).exists()
                alunos_com_checkin.append({
                    'aluno': aluno,
                    'has_checkin': has_checkin
                })
            alunos_por_atividade.append({
                'atividade': atividade,
                'alunos': alunos_com_checkin
            })
        context["alunos_por_atividade"] = alunos_por_atividade

        # Filtro baseado em parâmetros da URL
        if 'filter' in request.GET:
            filter_value = request.GET['filter']
            # Filtrar inscrições
            inscricoes_filtradas = [
                inscricao_info for inscricao_info in inscricoes_com_checkin
                if filter_value.lower() in inscricao_info['inscricao'].participante.nome.lower() or
                   filter_value.lower() in inscricao_info['inscricao'].participante.sobrenome.lower()
            ]
            context["inscricoes_com_checkin"] = inscricoes_filtradas

            # Filtrar alunos por atividade
            atividades_filtradas = []
            for atividade_info in alunos_por_atividade:
                alunos_filtrados = [
                    aluno_info for aluno_info in atividade_info['alunos']
                    if filter_value.lower() in aluno_info['aluno'].nome.lower() or
                       filter_value.lower() in aluno_info['aluno'].sobrenome.lower()
                ]
                if alunos_filtrados:
                    atividades_filtradas.append({
                        'atividade': atividade_info['atividade'],
                        'alunos': alunos_filtrados
                    })
            context["alunos_por_atividade"] = atividades_filtradas
    except Http404:
        # Caso não haja eventos disponíveis
        context["evento"] = None
        context["current_date"] = date.today()

    return render(request, "admin_checkin.html", context)

@login_required(login_url="/login")
def adminCheckinValidarAluno(request, pk_evento, pk_aluno, pk_atividade):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    handler = get_checkin_handler('aluno', request, pk_evento, pk_aluno, pk_atividade)
    return handler.validar()

@login_required(login_url="/login")
def adminCheckinValidarParticipante(request, pk_evento, pk_inscricao):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    handler = get_checkin_handler('participante', request, pk_evento, pk_inscricao)
    return handler.validar()

@login_required(login_url="/login")
def adminCheckinInvalidarAluno(request, pk_evento, pk_aluno, pk_atividade):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    handler = get_checkin_handler('aluno', request, pk_evento, pk_aluno, pk_atividade)
    return handler.invalidar()

@login_required(login_url="/login")
def adminCheckinInvalidarParticipante(request, pk_evento, pk_inscricao):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    handler = get_checkin_handler('participante', request, pk_evento, pk_inscricao)
    return handler.invalidar()


@login_required(login_url="/login")
def adminAtividade(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    professor = Professor.objects.filter(user=request.user).first()
    context = {}

    # Filtra atividades: exibe se o evento vinculado estiver ativo ou se não houver evento vinculado
    atividades_queryset = Atividade.objects.filter(Q(evento__ativo=True) | Q(evento__isnull=True))
    
    # Para a lista principal, mostra apenas as atividades vinculadas ao professor
    atividades_professor = atividades_queryset.filter(professores=professor)
    
    # Também usamos a queryset para preencher o <select> (exibindo todas as atividades ou, se preferir, os eventos ativos)
    context["eventos"] = atividades_queryset.distinct()
    context["atividades"] = atividades_professor

    if 'filter' in request.GET:
        filter_value = request.GET['filter']
        event_id = request.GET.get('event', '-1')
        filter_by = request.GET.get('filter_by', 'id')

        # Filtra pelo tópico da atividade
        atividades = atividades_queryset.filter(topico__icontains=filter_value)
        
        # Se o usuário selecionar um evento específico, filtra pelo ID do evento
        if event_id != '-1':
            atividades = atividades.filter(evento__pk=event_id)
        
        # Se o filtro for "Minhas Atividades", filtra pelas atividades do professor
        if filter_by == 'id':
            atividades = atividades.filter(professores=professor)
        
        context["atividades"] = atividades
        return render(request, "admin_atividade.html", context)

    if 'pk_atividade' in request.POST:
        atividade = Atividade.objects.filter(pk=request.POST['pk_atividade']).first()
        if atividade:
            atividade.delete()
        return redirect('adminAtividade')

    return render(request, "admin_atividade.html", context)

@login_required(login_url="/login")
def adminCadastrarAtividade(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')

    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.save()
            form.save_m2m()

            messages.success(request, "Atividade cadastrada com sucesso!")
            return redirect('adminAtividade')
    else:
        form = AtividadeForm()

    context = {'form': form}
    return render(request, 'admin_atividade_cadastrar.html', context)

@login_required(login_url="/login")
def adminVisualizarAtividade(request,pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    context["atividade"] = atividade = Atividade.objects.get(pk=pk)
    professor = Professor.objects.filter(user = request.user).first()
    form = AddParticipanteAtividadeForm(request.POST)
    form2 = AddAlunoAtividadeForm(request.POST)
    form3 = AddProfessorAtividadeForm(request.POST)

    if "pk_participante_remover" in request.POST:
        participante = Participante.objects.get(pk=request.POST["pk_participante_remover"])
        atividade.participantes.remove(participante)

    if "pk_aluno_remover" in request.POST:
        aluno = Aluno.objects.get(pk=request.POST["pk_aluno_remover"])
        atividade.alunos.remove(aluno)

    if "pk_professor_remover" in request.POST:
        professor = Professor.objects.get(pk=request.POST["pk_professor_remover"])
        atividade.professores.remove(professor)

    
    if request.method == 'POST':
        if form.is_valid():
            participante = form.cleaned_data['participante']
            atividade.participantes.add(participante)

            return redirect("adminVisualizarAtividade", pk=pk)

        if form2.is_valid():
            aluno = form2.cleaned_data['aluno']
            atividade.alunos.add(aluno)

            return redirect("adminVisualizarAtividade", pk=pk)
        
        if form3.is_valid():
            professor = form3.cleaned_data['professor']
            atividade.professores.add(professor)

            return redirect("adminVisualizarAtividade", pk=pk)
    else:
        form = AddParticipanteAtividadeForm()
        form2 = AddAlunoAtividadeForm()
        form3 = AddProfessorAtividadeForm()
    
    context["form"] = form
    context["form2"] = form2
    context["form3"] = form3
    context["size"] = atividade.professores.count()
    context["in_atividade"] = Atividade.objects.filter(pk=pk,professores__in=[professor]).exists()
    return render(request, "admin_atividade_visualizar.html", context)

@login_required(login_url='login')
def adminEditarAtividade(request, pk):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    atividade = get_object_or_404(Atividade,pk=pk)
    form = AtividadeForm(request.POST, instance=atividade)
    
    if request.method == "POST":
        if form.is_valid():
            atividade = form.save()
            #messages.success(request, f"Atividade Cadastrado com sucesso!")
            return redirect('adminAtividade')
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = AtividadeForm(instance=atividade)

    return render(request, 'admin_atividade_editar.html', context)


@login_required(login_url="/login")
def adminParticipante(request):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}

    # Subquery para buscar a instituição de cada participante
    instituicao_subquery = Instituicao.objects.filter(participantes=OuterRef('pk')).values('nome')[:1]
    
    # Anota cada participante com a instituição correspondente
    participantes = Participante.objects.annotate(instituicao_nome=Subquery(instituicao_subquery))
    
    context['participantes'] = participantes.order_by('id')

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
    participante = get_object_or_404(Participante, pk=pk)
    form = CustomUserForm(request.POST or None, instance=participante.user)
    form2 = ParticipanteForm(request.POST or None, instance=participante)

    if request.method == "POST":
        if form2.is_valid() and form.is_valid():
            # Salva o usuário e o participante
            user = form.save()
            participante = form2.save(commit=False)
            participante.user = user
            participante.save()

            # Atualiza a relação com a instituição
            instituicao = form2.cleaned_data.get('instituicao')
            if instituicao:
                # Remove o participante de todas as instituições e adiciona à nova
                participante.instituicao_set.clear()  # Remove todas as relações existentes
                instituicao.participantes.add(participante)  # Adiciona à nova instituição
            else:
                # Se nenhuma instituição for selecionada, remove o participante de todas as instituições
                participante.instituicao_set.clear()

            messages.success(request, "Participante atualizado com sucesso!")
            return redirect('adminParticipante')
        else:
            for error in list(form2.errors.values()):
                messages.error(request, error)

    context['form2'] = form2    
    context['form'] = form

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
            #messages.success(request, f"Atividade Cadastrado com sucesso!")
            return redirect('adminAluno')
        else:
            for error in list(form.errors.values()):
                pass

    context['form'] = AlunoForm(instance=aluno)

    return render(request, 'admin_aluno_editar.html', context)

@login_required(login_url="/login")
def adminInstituicao(request):
    instituicoes = Instituicao.objects.all()
    context = {'instituicoes': instituicoes}
    return render(request, 'admin_instituicao.html', context)

@login_required(login_url="/login")
def adminCadastrarInstituicao(request):
    if request.method == 'POST':
        form = InstituicaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Instituição cadastrada com sucesso.")
            return redirect('adminInstituicao')
    else:
        form = InstituicaoForm()
    context = {'form': form}
    return render(request, 'admin_instituicao_cadastrar.html', context)

@login_required(login_url="/login")
def adminEditarInstituicao(request, pk):
    instituicao = get_object_or_404(Instituicao, id=pk)
    if request.method == 'POST':
        form = InstituicaoForm(request.POST, instance=instituicao)
        if form.is_valid():
            form.save()
            messages.success(request, "Instituição atualizada com sucesso.")
            return redirect('adminInstituicao')
    else:
        form = InstituicaoForm(instance=instituicao)
    context = {'form': form}
    return render(request, 'admin_instituicao_editar.html', context)

@login_required(login_url="/login")
def adminVisualizarInstituicao(request, pk):
    instituicao = get_object_or_404(Instituicao, id=pk)
    participantes = instituicao.participantes.all()
    total_participantes = participantes.count()

    context = {
        'instituicao': instituicao,
        'participantes': participantes,
        'total_participantes': total_participantes,
    }
    return render(request, 'admin_instituicao_visualizar.html', context)

@login_required(login_url="/login")
def adminAvaliar(request, pk_atividade, pk_aluno):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    aluno = get_object_or_404(Aluno, pk=pk_aluno)
    atividade = get_object_or_404(Atividade, pk=pk_atividade)
    
    # Verifica se o aluno já realizou check-in na atividade
    checkin_exists = CheckIn.objects.filter(aluno=aluno, atividade=atividade).exists()
    
    avaliacoes = Avaliacao.objects.filter(aluno=aluno, atividade=atividade)
    
    if 'filter' in request.GET:
        filter_date = request.GET.get('filter')
        if filter_date:
            avaliacoes = avaliacoes.filter(dataAvaliacao=filter_date)
    
    if 'pk_avaliacao' in request.POST:
        avaliacao = avaliacoes.filter(pk=request.POST['pk_avaliacao']).first()
        if avaliacao:
            avaliacao.delete()
            messages.success(request, 'Avaliação excluída com sucesso!')
        else:
            messages.error(request, 'Avaliação não encontrada.')
        return redirect('adminAvaliar', pk_atividade=pk_atividade, pk_aluno=pk_aluno)
    
    context = {
        'aluno': aluno,
        'atividade': atividade,
        'avaliacoes': avaliacoes,
        'checkin_exists': checkin_exists,
    }
    
    return render(request, 'admin_avaliar_aluno.html', context)

@login_required(login_url='/login')
def adminCadastrarAvaliacao(request, pk_aluno, pk_atividade):
    if not request.user.validated:
        logout(request)
        return redirect('home')
    
    context = {}
    form = AvaliacaoForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            user = get_object_or_404(Aluno,pk=pk_aluno)
            atividade = get_object_or_404(Atividade,pk=pk_atividade)
            avaliacao = form.save(commit=False)
            avaliacao.dataAvaliacao = date.today()
            avaliacao.aluno = user
            avaliacao.atividade = atividade
            avaliacao.save()

            #messages.success(request, f"Cadastro realizado com sucesso, <b>{user.first_name}</b>!")
            return redirect('adminAvaliar', pk_aluno, pk_atividade)
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
            #messages.success(request, f"Atividade Cadastrado com sucesso!")
            return redirect('adminAvaliar', pk_atividade = avaliacao.atividade.id, pk_aluno = avaliacao.aluno.id)
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
    # Obtendo o evento atual
    context["evento"] = evento = Evento.objects.get_last_event()

    # Lista de participantes e alunos com check-in
    participantes_com_checkin = []
    alunos_com_checkin = []

    # Filtrar participantes com check-in
    inscricoes_com_checkin = Inscricao.objects.filter(evento=evento, checkin__isnull=False).distinct()
    participantes_com_checkin = [inscricao.participante for inscricao in inscricoes_com_checkin]

    # Filtrar alunos com check-in (se houver um modelo separado para alunos)
    alunos_com_checkin = [inscricao.participante for inscricao in inscricoes_com_checkin if hasattr(inscricao.participante, 'aluno')]

    context["participantes"] = participantes_com_checkin
    context["alunos"] = alunos_com_checkin
    context["eventos"] = Evento.objects.filter(ativo=1, data__lte=date.today())

    # Filtro baseado em parâmetros da URL
    if 'filter' in request.GET:
        filter_value = request.GET['filter']
        event_id = request.GET.get('event', "-1")

        if event_id == "-1":
            # Filtrar participantes e alunos com check-in para o evento atual
            participantes_filtrados = [p for p in participantes_com_checkin if filter_value.lower() in p.nome.lower() or filter_value.lower() in p.sobrenome.lower()]
            alunos_filtrados = [a for a in alunos_com_checkin if filter_value.lower() in a.nome.lower() or filter_value.lower() in a.sobrenome.lower()]
        else:
            # Filtrar participantes e alunos com check-in para o evento selecionado
            evento_selecionado = Evento.objects.get(id=event_id)
            inscricoes_filtradas = Inscricao.objects.filter(evento=evento_selecionado, checkin__isnull=False).distinct()
            participantes_filtrados = [inscricao.participante for inscricao in inscricoes_filtradas if filter_value.lower() in inscricao.participante.nome.lower() or filter_value.lower() in inscricao.participante.sobrenome.lower()]
            alunos_filtrados = [inscricao.participante for inscricao in inscricoes_filtradas if hasattr(inscricao.participante, 'aluno') and (filter_value.lower() in inscricao.participante.nome.lower() or filter_value.lower() in inscricao.participante.sobrenome.lower())]

        context["participantes"] = participantes_filtrados
        context["alunos"] = alunos_filtrados

    return render(request, "admin_certificados.html", context)


@login_required(login_url="/login")
def adminDownloadCertificado(request, pk_atividade, pk_participante):
    print(f"Buscando evento com pk={pk_atividade} e usuário com pk={pk_participante}")
    
    try:
        # pk_atividade representa o ID do Evento
        evento = get_object_or_404(Evento, pk=pk_atividade)
        print(f"Evento encontrado: {evento.tema}")
        
        # Buscando todas as atividades associadas ao evento
        atividades = Atividade.objects.filter(evento=evento)
        print(f"Atividades associadas ao evento: {atividades}")
        
        if not atividades.exists():
            print(f"Nenhuma atividade encontrada para o evento {evento.tema}")
            return HttpResponse("Nenhuma atividade associada a esse evento.", status=404)
        
        # Buscando o usuário com o pk fornecido
        usuario = get_object_or_404(Usuario, pk=pk_participante)
        print(f"Usuário encontrado: {usuario}")
    except Http404:
        print("Evento ou usuário não encontrado.")
        return HttpResponse("Evento ou usuário não encontrado.", status=404)
    
    # Buscando Aluno, Professor ou Participante associado ao usuário
    aluno = professor = participante = None
    try:
        aluno = Aluno.objects.get(user=usuario.user)
        print(f"Aluno encontrado: {aluno}")
    except Aluno.DoesNotExist:
        print("Aluno não encontrado para o usuário.")
    try:
        professor = Professor.objects.get(user=usuario.user)
        print(f"Professor encontrado: {professor}")
    except Professor.DoesNotExist:
        print("Professor não encontrado para o usuário.")
    try:
        participante = Participante.objects.get(user=usuario.user)
        print(f"Participante encontrado: {participante}")
    except Participante.DoesNotExist:
        print("Participante não encontrado para o usuário.")
    
    # Verificar se o usuário (como aluno, professor ou participante) está associado a alguma atividade
    atividade_encontrada = None
    for atividade in atividades:
        if (aluno and atividade.alunos.filter(pk=aluno.pk).exists()) or \
           (professor and atividade.professores.filter(pk=professor.pk).exists()) or \
           (participante and atividade.participantes.filter(pk=participante.pk).exists()):
            print(f"Usuário é aluno, professor ou participante da atividade: {atividade.topico}")
            atividade_encontrada = atividade
            break
    
    if not atividade_encontrada:
        print("Usuário não encontrado como aluno, professor ou participante em nenhuma atividade.")
        return HttpResponse("Usuário não encontrado como aluno, professor ou participante em nenhuma atividade.", status=404)
    
    # Buscar (ou gerar) o certificado usando o campo 'evento'
    certificado = Certificado.objects.filter(evento=evento, usuario=usuario).first()
    
    if certificado:
        print(f"Certificado já existe, caminho: {certificado.codigo}")
        pdf_path = certificado.codigo
    else:
        print("Certificado não encontrado, gerando novo...")
        date_time = atividade_encontrada.data.strftime("%d/%m/%Y")
        diff = atividade_encontrada.data - atividade_encontrada.data_cadastro
        semana = (diff.days // 7) * 14
        pdf_path = generateCertificado(usuario.nome + " " + usuario.sobrenome, atividade_encontrada.topico, date_time, str(semana))
        print(f"Certificado gerado, caminho: {pdf_path}")
        certificado = Certificado(dataEmissao=datetime.now(), codigo=pdf_path, evento=evento, usuario=usuario)
        certificado.save()
    
    try:
        with open(pdf_path, "rb") as pdf:
            print(f"Arquivo PDF encontrado: {pdf_path}")
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{atividade_encontrada.topico}_certificado.pdf"'
            return response
    except FileNotFoundError:
        print(f"Erro: arquivo PDF não encontrado em {pdf_path}")
        return HttpResponse("Certificado não encontrado.", status=404)
    
    print("Erro inesperado.")
    return HttpResponse("Erro inesperado", status=500)


@login_required(login_url="/login")
def certificados(request):
    context = {}
    context["participante"] = participante = Participante.objects.get(user=request.user.id)
    context["eventos"] = atividade = Atividade.objects.filter(inscricao__participante=participante, inscricao__checkin__isnull=False, data__lt=date.today()).distinct()
    print(atividade)
    

    return render(request, "certificados.html", context)

@login_required(login_url="/login")
def downloadCertificado(request, pk_atividade, pk_participante):
    # Primeiro tenta buscar com o pk_atividade original
    atividade = Atividade.objects.filter(pk=pk_atividade).first()

    # Se não encontrar, tenta com um outro ID (como 5 ou 6)
    if not atividade:
        atividade = Atividade.objects.filter(pk=5).first()  # ou pk=6

    if not atividade:
        # Caso não encontre nenhuma atividade, você pode lançar um erro ou retornar uma resposta adequada
        return HttpResponse("Atividade não encontrada", status=404)

    atividade = get_object_or_404(Atividade, pk=pk_atividade)
    participante = get_object_or_404(Participante, user=pk_participante)
    certificado = Certificado.objects.filter(atividade=atividade, usuario=participante)
    inscricao = Inscricao.objects.filter(atividade = atividade, participante = participante).first()
    check = CheckIn.objects.filter( inscricao = inscricao).first()

    if certificado:
        pdf_path = certificado.first().codigo
    else:
        if check:
            date_time = atividade.data.strftime("%d/%m/%Y")
            pdf_path = generateCertificado(participante.nome+" "+participante.sobrenome, atividade.tema, date_time, str(atividade.duracaoAtividade()))
            certificado = Certificado(dataEmissao=datetime.now(), codigo=pdf_path, atividade=atividade, usuario=participante)
            certificado.save()
        else:
            return redirect("certificados")
        
    with open(pdf_path, "rb") as pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="certificado.pdf"'
    return response

@login_required
def deleteItem(request, model, id):
    try:
        strategy = STRATEGIES.get(model.lower())
        if not strategy:
            raise ValueError("Model não suportado.")

        strategy.delete(id)
        print(f'{model} excluído com sucesso!')
        messages.success(request, f'{model} excluído com sucesso!')
    except Exception as e:
        print(f'Erro ao excluir: {str(e)}')
        messages.error(request, f'Erro ao excluir: {str(e)}')

    return redirect(request.META.get('HTTP_REFERER', 'home'))