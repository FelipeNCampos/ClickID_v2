"""
URLs para interface web do gerente
"""
from django.urls import path
from . import web_views
from . import web_views_modelos

app_name = 'web-gerente'

urlpatterns = [
    # Home
    path('', web_views.home, name='home'),
    
    # Autenticação
    path('login/', web_views.login_view, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
    
    # Dashboard Gerente
    path('dashboard/', web_views.gerente_dashboard, name='dashboard'),
    
    # Gerenciamento de Empresas
    path('empresas/', web_views.empresas_list, name='empresas-list'),
    path('empresas/nova/', web_views.empresa_create, name='empresa-create'),
    path('empresas/<uuid:pk>/', web_views.empresa_detail, name='empresa-detail'),
    path('empresas/<uuid:pk>/editar/', web_views.empresa_edit, name='empresa-edit'),
    path('empresas/<uuid:pk>/toggle-active/', web_views.empresa_toggle_active, name='empresa-toggle-active'),
    
    # Departamentos
    path('empresas/<uuid:empresa_pk>/departamentos/novo/', web_views.departamento_create, name='departamento-create'),
    path('empresas/<uuid:empresa_pk>/departamentos/<uuid:pk>/', web_views.departamento_detail, name='departamento-detail'),
    path('empresas/<uuid:empresa_pk>/departamentos/<uuid:pk>/editar/', web_views.departamento_edit, name='departamento-edit'),
    
    # Profissionais
    path('empresas/<uuid:empresa_pk>/profissionais/novo/', web_views.profissional_create, name='profissional-create'),
    path('empresas/<uuid:empresa_pk>/profissionais/importar/', web_views.profissional_import, name='profissional-import'),
    path('empresas/<uuid:empresa_pk>/profissionais/<uuid:pk>/', web_views.profissional_detail, name='profissional-detail'),
    path('empresas/<uuid:empresa_pk>/profissionais/<uuid:pk>/editar/', web_views.profissional_edit, name='profissional-edit'),
    path('empresas/<uuid:empresa_pk>/profissionais/<uuid:pk>/reset-senha/', web_views.profissional_reset_password, name='profissional-reset-password'),
    path('empresas/<uuid:empresa_pk>/profissionais/<uuid:pk>/toggle-active/', web_views.profissional_toggle_active, name='profissional-toggle-active'),
    path('empresas/<uuid:empresa_pk>/profissionais/<uuid:pk>/excluir/', web_views.profissional_delete, name='profissional-delete'),
    
    # Modelos
    path('empresas/<uuid:empresa_pk>/modelos/', web_views_modelos.modelos_list, name='modelos-list'),
    path('empresas/<uuid:empresa_pk>/modelos/novo/', web_views_modelos.modelo_create, name='modelo-create'),
    path('empresas/<uuid:empresa_pk>/modelos/<uuid:pk>/', web_views_modelos.modelo_detail, name='modelo-detail'),
    path('empresas/<uuid:empresa_pk>/modelos/<uuid:pk>/editar/', web_views_modelos.modelo_edit, name='modelo-edit'),
    path('empresas/<uuid:empresa_pk>/modelos/<uuid:pk>/canvas/', web_views_modelos.modelo_canvas_editor, name='modelo-canvas-editor'),
    path('empresas/<uuid:empresa_pk>/modelos/<uuid:pk>/excluir/', web_views_modelos.modelo_delete, name='modelo-delete'),
    path('empresas/<uuid:empresa_pk>/modelos/<uuid:pk>/toggle-active/', web_views_modelos.modelo_toggle_active, name='modelo-toggle-active'),
    
    # Departamentos - Ações
    path('empresas/<uuid:empresa_pk>/departamentos/<uuid:pk>/excluir/', web_views.departamento_delete, name='departamento-delete'),
    
    # Coletas - Gerente pode gerenciar todas as coletas
    path('coletas/', web_views.gerente_coletas_list, name='coletas-list'),
    path('coletas/<uuid:pk>/', web_views.gerente_coleta_detail, name='coleta-detail'),
    path('coletas/<uuid:pk>/gerenciar/', web_views.gerente_coleta_manage, name='coleta-manage'),
    path('coletas/<uuid:pk>/cancelar/', web_views.gerente_coleta_cancelar, name='coleta-cancelar'),
    path('coletas/<uuid:pk>/exportar/', web_views.gerente_coleta_exportar, name='coleta-exportar'),
    path('coletas/<uuid:pk>/exportar-dados-textuais/', web_views.gerente_coleta_exportar_dados_textuais, name='coleta-exportar-dados-textuais'),
    path('coletas/<uuid:pk>/exportar-participantes/', web_views.gerente_coleta_exportar_participantes, name='coleta-exportar-participantes'),
    path('coletas/<uuid:pk>/exportar-midias/', web_views.gerente_coleta_exportar_midias, name='coleta-exportar-midias'),
    path('coletas/<uuid:pk>/remover-participante/', web_views.gerente_coleta_remover_participante, name='coleta-remover-participante'),
    path('coletas/<uuid:pk>/refazer/', web_views.gerente_coleta_refazer, name='coleta-refazer'),
    path('coletas/<uuid:pk>/refazer-individual/', web_views.gerente_coleta_refazer_individual, name='coleta-refazer-individual'),
    
    # Logs de auditoria
    path('logs/', web_views.logs_auditoria, name='logs'),
]
