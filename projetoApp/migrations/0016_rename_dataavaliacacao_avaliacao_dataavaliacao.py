# Generated by Django 4.2.6 on 2023-11-22 02:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projetoApp', '0015_alter_exibicao_alunos_alter_exibicao_professores'),
    ]

    operations = [
        migrations.RenameField(
            model_name='avaliacao',
            old_name='dataAvaliacacao',
            new_name='dataAvaliacao',
        ),
    ]
