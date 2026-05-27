"""
URLs para interface web de coleta (profissional)
"""
from django.urls import path
from . import web_views

app_name = 'web-coleta'

urlpatterns = [
    # Acesso por token
    path('<str:token>/', web_views.coleta_acesso, name='acesso'),
    path('<str:token>/preencher/', web_views.coleta_preencher, name='preencher'),
    path('<str:token>/confirmar/', web_views.coleta_confirmar, name='confirmar'),
    path('<str:token>/sucesso/', web_views.coleta_sucesso, name='sucesso'),
    # Visualizar respostas de participante de coleta
    path('coletas/<uuid:coleta_id>/participantes/<uuid:usuario_id>/respostas/', web_views.participante_respostas, name='participante-respostas'),
]
