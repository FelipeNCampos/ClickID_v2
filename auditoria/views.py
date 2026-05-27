""""
Views/ViewSets for auditoria app
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import LogAuditoria
from .serializers import LogAuditoriaSerializer
from clickid_core.db_utils import get_request_params


class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para LogAuditoria (somente leitura)"""
    queryset = LogAuditoria.objects.select_related('usuario', 'empresa', 'coleta').all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['usuario_nome', 'descricao', 'tipo_acao']
    ordering_fields = ['data_hora']
    ordering = ['-data_hora']
    
    def get_queryset(self):
        user = self.request.user
        queryset = LogAuditoria.objects.select_related('usuario', 'empresa', 'coleta').all()
        
        # Filtrar por empresa
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                queryset = queryset.filter(empresa=empresa)
            except Empresa.DoesNotExist:
                return LogAuditoria.objects.none()
        elif user.tipo_usuario == 'profissional':
            return LogAuditoria.objects.none()
        
        # Filtros
        params = get_request_params(self.request)
        empresa_id = params.get('empresa_id')
        coleta_id = params.get('coleta_id')
        tipo_acao = params.get('tipo_acao')
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        if coleta_id:
            queryset = queryset.filter(coleta_id=coleta_id)
        if tipo_acao:
            queryset = queryset.filter(tipo_acao=tipo_acao)
        
        return queryset
