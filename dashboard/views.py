"""
Views/ViewSets for dashboard app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from .models import Dashboard, Relatorio, Estatistica, Alerta
from .serializers import (
    DashboardSerializer, DashboardConfigSerializer,
    RelatorioSerializer, RelatorioListSerializer, RelatorioCreateSerializer,
    EstatisticaSerializer, EstatisticaRangeSerializer,
    AlertaSerializer, AlertaListSerializer,
    DashboardWidgetSerializer, DashboardEstatisticasGeraisSerializer
)
from clickid_core.db_utils import get_request_params


class DashboardViewSet(viewsets.ModelViewSet):
    """ViewSet para Dashboard"""
    queryset = Dashboard.objects.select_related('empresa').all()
    serializer_class = DashboardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Dashboard.objects.select_related('empresa').all()
        
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                queryset = queryset.filter(empresa=empresa)
            except Empresa.DoesNotExist:
                return Dashboard.objects.none()
        elif user.tipo_usuario == 'profissional':
            return Dashboard.objects.none()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Obter estatísticas do dashboard"""
        dashboard = self.get_object()
        estatisticas = dashboard.obter_estatisticas()
        
        # Adicionar alertas não lidos
        alertas_nao_lidos = Alerta.objects.filter(
            empresa=dashboard.empresa,
            lido=False
        ).count()
        
        estatisticas['alertas_nao_lidos'] = alertas_nao_lidos
        estatisticas['ultimas_atividades'] = []  # TODO: Implementar
        
        serializer = DashboardEstatisticasGeraisSerializer(estatisticas)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def configurar(self, request, pk=None):
        """Atualizar configurações do dashboard"""
        dashboard = self.get_object()
        serializer = DashboardConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        for key, value in serializer.validated_data.items():
            setattr(dashboard, key, value)
        dashboard.save()
        
        return Response(DashboardSerializer(dashboard).data)
    
    @action(detail=True, methods=['post'])
    def adicionar_widget(self, request, pk=None):
        """Adicionar widget ao dashboard"""
        dashboard = self.get_object()
        serializer = DashboardWidgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        widget_id = serializer.validated_data['widget_id']
        config = serializer.validated_data.get('config', {})
        
        dashboard.adicionar_widget(widget_id, config)
        
        return Response({'message': 'Widget adicionado com sucesso.'})
    
    @action(detail=True, methods=['post'])
    def remover_widget(self, request, pk=None):
        """Remover widget do dashboard"""
        dashboard = self.get_object()
        serializer = DashboardWidgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        widget_id = serializer.validated_data['widget_id']
        dashboard.remover_widget(widget_id)
        
        return Response({'message': 'Widget removido com sucesso.'})
    
    @action(detail=True, methods=['post'])
    def resetar(self, request, pk=None):
        """Resetar dashboard para configuração padrão"""
        dashboard = self.get_object()
        dashboard.resetar_layout()
        return Response({'message': 'Dashboard resetado para configuração padrão.'})


class RelatorioViewSet(viewsets.ModelViewSet):
    """ViewSet para Relatorio"""
    queryset = Relatorio.objects.select_related('empresa', 'gerado_por').all()
    serializer_class = RelatorioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RelatorioListSerializer
        elif self.action == 'create':
            return RelatorioCreateSerializer
        return RelatorioSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Relatorio.objects.select_related('empresa', 'gerado_por').all()
        
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                queryset = queryset.filter(empresa=empresa)
            except Empresa.DoesNotExist:
                return Relatorio.objects.none()
        elif user.tipo_usuario == 'profissional':
            return Relatorio.objects.none()
        
        # Filtros
        params = get_request_params(self.request)
        tipo = params.get('tipo')
        status_filter = params.get('status')
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        """Criar relatório e iniciar geração"""
        relatorio = serializer.save(
            gerado_por=self.request.user,
            empresa=self.get_empresa()
        )
        
        # Disparar geração assíncrona
        relatorio.gerar()
    
    def get_empresa(self):
        """Obter empresa do usuário"""
        user = self.request.user
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            return Empresa.objects.get(usuario=user)
        return None
    
    @action(detail=True, methods=['post'])
    def baixar(self, request, pk=None):
        """Baixar arquivo do relatório"""
        relatorio = self.get_object()
        
        if not relatorio.arquivo:
            return Response(
                {'error': 'Relatório ainda não foi gerado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'url': relatorio.arquivo.url,
            'nome_arquivo': relatorio.arquivo.name.split('/')[-1]
        })
    
    @action(detail=True, methods=['post'])
    def renovar(self, request, pk=None):
        """Renovar expiração do relatório"""
        relatorio = self.get_object()
        relatorio.renovar_expiracao()
        return Response({'message': 'Expiração renovada por 30 dias.'})
    
    @action(detail=False, methods=['post'])
    def limpar_expirados(self, request):
        """Limpar relatórios expirados"""
        count = Relatorio.limpar_expirados()
        return Response({'message': f'{count} relatório(s) expirado(s) removido(s).'})


class AlertaViewSet(viewsets.ModelViewSet):
    """ViewSet para Alerta"""
    queryset = Alerta.objects.select_related('empresa', 'coleta', 'profissional').all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AlertaListSerializer
        return AlertaSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Alerta.objects.select_related('empresa', 'coleta', 'profissional').all()
        
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                queryset = queryset.filter(empresa=empresa)
            except Empresa.DoesNotExist:
                return Alerta.objects.none()
        elif user.tipo_usuario == 'profissional':
            return Alerta.objects.none()
        
        # Filtros
        params = get_request_params(self.request)
        lido = params.get('lido')
        resolvido = params.get('resolvido')
        tipo = params.get('tipo')
        severidade = params.get('severidade')
        
        if lido is not None:
            queryset = queryset.filter(lido=lido.lower() == 'true')
        if resolvido is not None:
            queryset = queryset.filter(resolvido=resolvido.lower() == 'true')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if severidade:
            queryset = queryset.filter(severidade=severidade)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def marcar_lido(self, request, pk=None):
        """Marcar alerta como lido"""
        alerta = self.get_object()
        alerta.marcar_lido()
        return Response({'message': 'Alerta marcado como lido.'})
    
    @action(detail=True, methods=['post'])
    def marcar_resolvido(self, request, pk=None):
        """Marcar alerta como resolvido"""
        alerta = self.get_object()
        alerta.marcar_resolvido()
        return Response({'message': 'Alerta marcado como resolvido.'})
    
    @action(detail=False, methods=['post'])
    def marcar_todos_lidos(self, request):
        """Marcar todos os alertas como lidos"""
        from empresas.models import Empresa
        try:
            empresa = Empresa.objects.get(usuario=request.user)
            count = Alerta.objects.filter(
                empresa=empresa,
                lido=False
            ).update(lido=True)
            return Response({'message': f'{count} alerta(s) marcado(s) como lido(s).'})
        except Empresa.DoesNotExist:
            return Response({'error': 'Empresa não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

