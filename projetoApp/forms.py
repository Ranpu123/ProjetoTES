
from django import forms
from .models import CustomUser, Participante, Professor, Aluno, Evento, Exibicao, Avaliacao
from .customWidgets import DateInput
from bootstrap_datepicker_plus.widgets import TimePickerInput, DatePickerInput
from django.db.models.functions import Concat  
from django.db.models import Value as V

class CustomUserForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput)
    class Meta:
        model = CustomUser
        fields = ['email']
    
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(CustomUserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class ParticipanteForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = ['nome', 'sobrenome', 'CPF']
        exclude = ['user']

class ProfessorForm(forms.ModelForm):
    class Meta:
        model = Professor
        fields = ['nome', 'sobrenome', 'CPF']
        exclude = ['user']

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'sobrenome', 'CPF']
        exclude = ['user']

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'
        exclude = ['ativo']
        widgets = {'data': DatePickerInput(), 'horario_fim': TimePickerInput(), 'horario_inicio': TimePickerInput()}
    
    def get_inital_data():
        initial_data = {
            'horario_inicio': "8:00",
            'horario_fim': "18:00",
            'logradouro': "R. Pref. Brásílio Ribas, 775",
            'bairro': "São José",
            'cidade': "Ponta Grossa",
            'estado': "Paraná",
            'banner': "https://www.lifecaretechnology.com/wp-content/uploads/2018/12/default-banner.jpg",
        }
        return initial_data

class ExibicaoForm(forms.ModelForm):
    class Meta:
        model = Exibicao
        exclude = ['alunos', 'professores','data_cadastro']

class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        exclude = ['aluno', 'exibicao', "dataAvaliacao"]

class AddAlunoExibicaoForm(forms.Form):
    aluno = forms.ModelChoiceField(queryset=Aluno.objects.all(), label='Adicionar Aluno')

class AddProfessorExibicaoForm(forms.Form):
    professor = forms.ModelChoiceField(queryset=Professor.objects.all(), label='Adicionar Professor')