"""
Views/ViewSets for usuarios app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Usuario, Gerente, LogAuditoria
from clickid_core.db_utils import get_request_params
from .serializers import (
    UsuarioSerializer, GerenteSerializer, GerenteDetailSerializer,
    LogAuditoriaSerializer, LoginSerializer, PasswordChangeSerializer,
    PasswordResetSerializer
)


class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para Usuario"""
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.tipo_usuario == 'gerente':
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Retorna dados do usuário logado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Endpoint de login"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UsuarioSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Alterar senha"""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Senha alterada com sucesso.'})
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """Solicitar recuperação de senha"""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Implementar envio de email com Celery
        return Response({
            'message': 'Email de recuperação enviado.'
        })


class GerenteViewSet(viewsets.ModelViewSet):
    """ViewSet para Gerente"""
    queryset = Gerente.objects.select_related('usuario').all()
    serializer_class = GerenteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GerenteDetailSerializer
        return GerenteSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.tipo_usuario == 'gerente':
            return Gerente.objects.select_related('usuario').all()
        return Gerente.objects.filter(usuario=user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Ativar/desativar gerente"""
        gerente = self.get_object()
        gerente.is_active = not gerente.is_active
        gerente.save()
        
        return Response({
            'message': f'Gerente {"ativado" if gerente.is_active else "desativado"} com sucesso.',
            'is_active': gerente.is_active
        })


class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para LogAuditoria (somente leitura)"""
    queryset = LogAuditoria.objects.select_related('usuario').all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or user.tipo_usuario == 'gerente'):
            return LogAuditoria.objects.none()
        
        queryset = LogAuditoria.objects.select_related('usuario').all()
        
        # Filtros
        params = get_request_params(self.request)
        usuario_id = params.get('usuario_id')
        acao = params.get('acao')
        data_inicio = params.get('data_inicio')
        data_fim = params.get('data_fim')
        
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        if acao:
            queryset = queryset.filter(acao=acao)
        if data_inicio:
            queryset = queryset.filter(timestamp__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(timestamp__lte=data_fim)
        
        return queryset

