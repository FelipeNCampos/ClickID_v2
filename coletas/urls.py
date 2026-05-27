"""
URLs for coletas app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ColetaViewSet, ColetaProfissionalViewSet, RespostaColetaViewSet,
    NotificacaoViewSet
)

router = DefaultRouter()
router.register(r'coletas', ColetaViewSet, basename='coleta')
router.register(r'coletas-profissionais', ColetaProfissionalViewSet, basename='coleta-profissional')
router.register(r'respostas-coletas', RespostaColetaViewSet, basename='resposta-coleta')
router.register(r'notificacoes', NotificacaoViewSet, basename='notificacao')

app_name = 'coletas'

urlpatterns = [
    path('', include(router.urls)),
]
