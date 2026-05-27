"""
URLs for dashboard app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet, RelatorioViewSet, AlertaViewSet

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'relatorios', RelatorioViewSet, basename='relatorio')
router.register(r'alertas', AlertaViewSet, basename='alerta')

app_name = 'dashboard'

urlpatterns = [
    path('', include(router.urls)),
]
