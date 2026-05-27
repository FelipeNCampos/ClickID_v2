"""
URLs for empresas app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmpresaViewSet, DepartamentoViewSet, ProfissionalViewSet

router = DefaultRouter()
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'profissionais', ProfissionalViewSet, basename='profissional')

app_name = 'empresas'

urlpatterns = [
    path('', include(router.urls)),
]
