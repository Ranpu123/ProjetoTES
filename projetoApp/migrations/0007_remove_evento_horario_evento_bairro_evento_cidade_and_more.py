# Generated by Django 4.2.6 on 2023-11-19 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projetoApp', '0006_alter_customuser_options_rename_cpf_usuario_cpf_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evento',
            name='horario',
        ),
        migrations.AddField(
            model_name='evento',
            name='bairro',
            field=models.CharField(default='São José', max_length=255, verbose_name='Bairro'),
        ),
        migrations.AddField(
            model_name='evento',
            name='cidade',
            field=models.CharField(default='Ponta Grossa', max_length=50, verbose_name='Cidade'),
        ),
        migrations.AddField(
            model_name='evento',
            name='estado',
            field=models.CharField(default='Paraná', max_length=50, verbose_name='UF'),
        ),
        migrations.AddField(
            model_name='evento',
            name='harario_fim',
            field=models.TimeField(blank=True, default='18:00', verbose_name='Horario Fim'),
        ),
        migrations.AddField(
            model_name='evento',
            name='horario_inicio',
            field=models.TimeField(blank=True, default='8:00', verbose_name='Horario Inicio'),
        ),
        migrations.AddField(
            model_name='evento',
            name='logradouro',
            field=models.CharField(default='R. Pref. Brásílio Ribas, 775', max_length=255, verbose_name='Logradouro'),
        ),
    ]
