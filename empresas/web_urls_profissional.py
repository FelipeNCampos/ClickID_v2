"""
URLs para interface web do profissional/empresa
Login com CPF e dashboard de formulários
"""
from django.urls import path
from empresas import web_views_profissional

app_name = 'profissional'

urlpatterns = [
    # Autenticação
    path('login/', web_views_profissional.profissional_login, name='login'),
    path('logout/', web_views_profissional.profissional_logout, name='logout'),
    
    # Dashboard
    path('', web_views_profissional.profissional_dashboard, name='dashboard'),
    
    # Alteração de senha
    path('alterar-senha/', web_views_profissional.profissional_alterar_senha, name='alterar-senha'),
    
    # Coletas
    path('coletas/<uuid:pk>/', web_views_profissional.profissional_coleta_detail, name='coleta-detail'),
    path('coletas/<uuid:pk>/preencher/', web_views_profissional.profissional_coleta_preencher, name='coleta-preencher'),
]
