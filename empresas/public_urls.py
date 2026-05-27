"""
URLs públicas para páginas de empresas
"""
from django.urls import path
from . import public_views

urlpatterns = [
    path('', public_views.empresa_public_page, name='empresa-public'),
]
