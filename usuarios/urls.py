"""
URLs for usuarios app API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'gerentes', views.GerenteViewSet, basename='gerente')
router.register(r'logs-auditoria', views.LogAuditoriaViewSet, basename='log-auditoria')

urlpatterns = [
    # Router URLs (inclui /usuarios/login/, /usuarios/me/, etc.)
    path('', include(router.urls)),
    
    # JWT Token Refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
