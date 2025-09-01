from django.db import migrations
from django.contrib.auth.hashers import make_password

def add_test_users(apps, schema_editor):
    # Obtém o modelo CustomUser do estado da migração
    CustomUser = apps.get_model('projetoApp', 'CustomUser')
    
    # Cria os usuários de teste
    # Usuário 1: Admin
    if not CustomUser.objects.filter(email='teste@teste.com').exists():
        CustomUser.objects.create(
            id=3,
            password='pbkdf2_sha256$600000$QUcxVPDnGtwyWOvR7eBKJG$jEKolCDMYIQuPd/bVh9YGdvKfNSZDn/vupipMwpeZU8=',
            last_login='2024-10-08 21:44:12.238368',
            first_name='',
            last_name='',
            username='',
            email='teste@teste.com',
            validated=True,
            date_joined='2023-11-19 21:08:41.627844',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
    
    # Usuário 2: Aluno
    if not CustomUser.objects.filter(email='carlos@bol.com').exists():
        CustomUser.objects.create(
            id=14,
            password='pbkdf2_sha256$600000$QUcxVPDnGtwyWOvR7eBKJG$jEKolCDMYIQuPd/bVh9YGdvKfNSZDn/vupipMwpeZU8=',
            last_login='2024-10-08 21:13:01.737250',
            first_name='Carlos',
            last_name='Albuquerque',
            username='',
            email='carlos@bol.com',
            validated=False,
            date_joined='2023-11-22 03:14:56.915334',
            is_active=True,
            is_staff=False,
            is_superuser=False
        )

def remove_test_users(apps, schema_editor):
    # Obtém o modelo CustomUser do estado da migração
    CustomUser = apps.get_model('projetoApp', 'CustomUser')
    
    # Remove os usuários de teste
    CustomUser.objects.filter(email='teste@teste.com').delete()
    CustomUser.objects.filter(email='carlos@bol.com').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('projetoApp', '0008_alter_avaliacao_descricao_alter_checkin_aluno'),
    ]

    operations = [
        migrations.RunPython(add_test_users, remove_test_users),
    ]