"""
URLs for modelos app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModeloCartaoViewSet, CampoCartaoViewSet

router = DefaultRouter()
router.register(r'modelos-cartao', ModeloCartaoViewSet, basename='modelo-cartao')
router.register(r'campos-cartao', CampoCartaoViewSet, basename='campo-cartao')

app_name = 'modelos'

urlpatterns = [
    path('', include(router.urls)),
]
