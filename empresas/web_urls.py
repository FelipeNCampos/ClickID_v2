"""
URLs para interface web da empresa
"""
from django.urls import path
from . import web_views
from coletas import web_views as coletas_web_views

app_name = 'web-empresa'

urlpatterns = [
    # Dashboard Empresa
    path('dashboard/', web_views.empresa_dashboard, name='dashboard'),
    
    # Departamentos
    path('departamentos/', web_views.departamentos_list, name='departamentos-list'),
    path('departamentos/novo/', web_views.departamento_create, name='departamento-create'),
    
    # Profissionais
    path('profissionais/', web_views.profissionais_list, name='profissionais-list'),
    path('profissionais/novo/', web_views.profissional_create, name='profissional-create'),
    path('profissionais/importar/', web_views.profissionais_import, name='profissionais-import'),
    path('profissionais/importar-dados/', web_views.profissionais_import_dados, name='profissionais-import-dados'),
    path('profissionais/<uuid:pk>/', web_views.profissional_detail, name='profissional-detail'),
    # The edit form is rendered/handled by `profissional_detail` (no separate profissional_edit function)
    path('profissionais/<uuid:pk>/editar/', web_views.profissional_detail, name='profissional-edit'),
    path('profissionais/<uuid:pk>/toggle-active/', web_views.profissional_toggle_active, name='profissional-toggle-active'),
    path('profissionais/<uuid:pk>/excluir/', web_views.profissional_delete, name='profissional-delete'),
    
    # Modelos de Cartão
    path('modelos/', web_views.modelos_list, name='modelos-list'),
    path('modelos/novo/', web_views.modelo_create, name='modelo-create'),
    path('modelos/<uuid:pk>/', web_views.modelo_detail, name='modelo-detail'),
    path('modelos/<uuid:pk>/editar/', web_views.modelo_edit, name='modelo-edit'),
    path('modelos/<uuid:pk>/duplicar/', web_views.modelo_duplicate, name='modelo-duplicate'),
    
    # Coletas
    path('coletas/', web_views.coletas_list, name='coletas-list'),
    path('coletas/nova/', web_views.coleta_create, name='coleta-create'),
    path('coletas/<uuid:pk>/', web_views.coleta_detail, name='coleta-detail'),
    path('coletas/<uuid:pk>/gerenciar/', web_views.coleta_manage, name='coleta-manage'),
    path('coletas/<uuid:pk>/cancelar/', web_views.coleta_cancelar, name='coleta-cancelar'),
    path('coletas/<uuid:pk>/apagar/', web_views.coleta_apagar, name='coleta-apagar'),
    path('coletas/<uuid:pk>/exportar/', web_views.coleta_exportar, name='coleta-exportar'),
    path('coletas/<uuid:pk>/exportar-dados-textuais/', web_views.coleta_exportar_dados_textuais, name='coleta-exportar-dados-textuais'),
    path('coletas/<uuid:pk>/exportar-participantes/', web_views.coleta_exportar_participantes, name='coleta-exportar-participantes'),
    path('coletas/<uuid:pk>/exportar-midias/', web_views.coleta_exportar_midias, name='coleta-exportar-midias'),
    path('coletas/<uuid:pk>/remover-participante/', web_views.coleta_remover_participante, name='coleta-remover-participante'),
    path('coletas/<uuid:pk>/refazer/', web_views.coleta_refazer, name='coleta-refazer'),
    path('coletas/<uuid:pk>/refazer-individual/', web_views.coleta_refazer_individual, name='coleta-refazer-individual'),
    # Visualizar respostas do participante (usa view do app coletas)
    path('coletas/<uuid:coleta_id>/participantes/<uuid:usuario_id>/respostas/', coletas_web_views.participante_respostas, name='participante-respostas'),
    
    # Logs de Auditoria
    path('logs/', web_views.logs_auditoria, name='logs'),
]
