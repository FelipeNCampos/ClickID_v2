"""
URL configuration for clickid_core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Site Web - Páginas principais
    path('', RedirectView.as_view(pattern_name='web-gerente:home', permanent=False)),
    path('gerente/', include('usuarios.web_urls', namespace='web-gerente')),
    path('empresa/', include('empresas.web_urls', namespace='web-empresa')),
    path('profissional/', include('empresas.web_urls_profissional', namespace='profissional')),
    path('coleta/', include('coletas.web_urls', namespace='web-coleta')),
    
    # API v1
    path('api/v1/', include([
        path('', include('usuarios.urls')),
        path('', include('empresas.urls')),
        path('', include('modelos.urls')),
        path('', include('coletas.urls')),
        path('', include('dashboard.urls')),
        path('auditoria/', include('auditoria.urls')),
    ])),
    
    # Página pública da empresa (deve ser a última)
    path('<slug:url_personalizada>/', include('empresas.public_urls')),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

