"""
Views/ViewSets for modelos app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import ModeloCartao, CampoCartao, TipoCampo
from .serializers import (
    ModeloCartaoSerializer, ModeloCartaoListSerializer,
    ModeloCartaoCreateSerializer, ModeloCartaoDuplicateSerializer,
    CampoCartaoSerializer, CampoCartaoListSerializer,
    CampoCartaoReorderSerializer, TipoCampoSerializer
)
from clickid_core.db_utils import get_request_params


class ModeloCartaoViewSet(viewsets.ModelViewSet):
    """ViewSet para ModeloCartao"""
    queryset = ModeloCartao.objects.prefetch_related('campos').all()
    serializer_class = ModeloCartaoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ModeloCartaoListSerializer
        elif self.action == 'create':
            return ModeloCartaoCreateSerializer
        return ModeloCartaoSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = ModeloCartao.objects.prefetch_related('campos').all()
        
        # Filtrar por empresa do usuário
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                queryset = queryset.filter(empresa=empresa)
            except Empresa.DoesNotExist:
                return ModeloCartao.objects.none()
        elif user.tipo_usuario == 'profissional':
            from empresas.models import Profissional
            try:
                profissional = Profissional.objects.get(usuario=user)
                queryset = queryset.filter(empresa=profissional.empresa)
            except Profissional.DoesNotExist:
                return ModeloCartao.objects.none()
        # Gerentes podem ver todos os modelos (sem filtro adicional)
        
        # Filtros
        params = get_request_params(self.request)
        empresa_id = params.get('empresa') or params.get('empresa_id')
        is_active = params.get('is_active')
        
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_update(self, serializer):
        """Validar que usuário pode editar o modelo"""
        user = self.request.user
        modelo = self.get_object()
        
        # Empresas só podem editar seus próprios modelos
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                if modelo.empresa != empresa:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied('Você não tem permissão para editar este modelo.')
            except Empresa.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Empresa não encontrada.')
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Validar que usuário pode deletar o modelo"""
        user = self.request.user
        
        # Empresas só podem deletar seus próprios modelos
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa = Empresa.objects.get(usuario=user)
                if instance.empresa != empresa:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied('Você não tem permissão para deletar este modelo.')
            except Empresa.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Empresa não encontrada.')
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        """Duplicar modelo"""
        modelo_original = self.get_object()
        serializer = ModeloCartaoDuplicateSerializer(
            data=request.data,
            context={'empresa': modelo_original.empresa}
        )
        serializer.is_valid(raise_exception=True)
        
        novo_nome = serializer.validated_data['novo_nome']
        copiar_campos = serializer.validated_data['copiar_campos']
        
        # Criar cópia do modelo
        novo_modelo = ModeloCartao.objects.create(
            empresa=modelo_original.empresa,
            nome=novo_nome,
            descricao=modelo_original.descricao,
            largura_mm=modelo_original.largura_mm,
            altura_mm=modelo_original.altura_mm,
            dpi=modelo_original.dpi,
            background_image=modelo_original.background_image,
            background_color=modelo_original.background_color,
            is_active=True
        )
        
        # Copiar campos se solicitado
        if copiar_campos:
            campos_originais = modelo_original.campos.all()
            for campo in campos_originais:
                CampoCartao.objects.create(
                    modelo=novo_modelo,
                    nome_campo=campo.nome_campo,
                    tipo=campo.tipo,
                    obrigatorio=campo.obrigatorio,
                    ordem=campo.ordem,
                    pergunta_formulario=campo.pergunta_formulario,
                    placeholder=campo.placeholder,
                    texto_ajuda=campo.texto_ajuda,
                    opcoes=campo.opcoes,
                    validacao_regex=campo.validacao_regex,
                    posicao_x=campo.posicao_x,
                    posicao_y=campo.posicao_y,
                    largura=campo.largura,
                    altura=campo.altura,
                    fonte=campo.fonte,
                    tamanho_fonte=campo.tamanho_fonte,
                    cor_texto=campo.cor_texto,
                    alinhamento=campo.alinhamento,
                    negrito=campo.negrito,
                    italico=campo.italico,
                    sublinhado=campo.sublinhado,
                    rotacao=campo.rotacao
                )
        
        return Response(
            ModeloCartaoSerializer(novo_modelo).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Gerar preview do modelo"""
        modelo = self.get_object()
        # TODO: Implementar geração de preview com Pillow
        return Response({
            'message': 'Preview será gerado',
            'modelo': ModeloCartaoSerializer(modelo).data
        })


class CampoCartaoViewSet(viewsets.ModelViewSet):
    """ViewSet para CampoCartao"""
    queryset = CampoCartao.objects.select_related('modelo').all()
    serializer_class = CampoCartaoSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Criar campo com logging de erros"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Dados recebidos para criar campo: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Erro ao criar campo: {str(e)}")
            logger.error(f"Erros de validação: {serializer.errors if hasattr(serializer, 'errors') else 'N/A'}")
            raise
    
    def update(self, request, *args, **kwargs):
        """Atualizar modelo de cartão, aceitando PATCH parcial para upload de imagem/cor de fundo"""
        import logging
        logger = logging.getLogger(__name__)

        partial = True  # Forçar PATCH parcial para aceitar FormData
        instance = self.get_object()

        logger.info(f"Dados recebidos para atualizar modelo {instance.id}: {request.data}")

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Erro ao atualizar modelo: {str(e)}")
            logger.error(f"Erros de validação: {serializer.errors if hasattr(serializer, 'errors') else 'N/A'}")
            raise
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CampoCartaoListSerializer
        return CampoCartaoSerializer
    
    def perform_create(self, serializer):
        """Garantir que o campo seja criado apenas no contexto do modelo atual"""
        modelo = serializer.validated_data.get('modelo')
        if CampoCartao.objects.filter(modelo=modelo, nome_campo=serializer.validated_data.get('nome_campo')).exists():
            raise ValueError(f"Já existe um campo com o nome '{serializer.validated_data.get('nome_campo')}' neste modelo.")
        serializer.save()

    def perform_update(self, serializer):
        """Garantir que o campo seja atualizado apenas no contexto do modelo atual"""
        modelo = serializer.validated_data.get('modelo')
        if CampoCartao.objects.filter(modelo=modelo, nome_campo=serializer.validated_data.get('nome_campo')).exclude(id=self.get_object().id).exists():
            raise ValueError(f"Já existe um campo com o nome '{serializer.validated_data.get('nome_campo')}' neste modelo.")
        serializer.save()

    def get_queryset(self):
        """Filtrar campos apenas do modelo atual"""
        params = get_request_params(self.request)
        modelo_id = params.get('modelo_id')
        queryset = CampoCartao.objects.select_related('modelo').all()
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)
        return queryset

    def get_queryset(self):
        user = self.request.user
        queryset = CampoCartao.objects.select_related('modelo').all()
        # (debug prints removed)
        
        # Determine empresa context from the authenticated user (Empresa or Profissional)
        # If the user is a gerente we keep full access; otherwise restrict to their empresa.
        from empresas.models import Empresa, Profissional
        try:
            empresa = Empresa.objects.get(usuario=user)
            queryset = queryset.filter(modelo__empresa=empresa)
        except Empresa.DoesNotExist:
            try:
                prof = Profissional.objects.select_related('empresa').get(usuario=user)
                queryset = queryset.filter(modelo__empresa=prof.empresa)
            except Profissional.DoesNotExist:
                # If the user is explicitly a 'gerente' allow access to all; otherwise deny.
                if getattr(user, 'tipo_usuario', None) == 'gerente':
                    pass
                else:
                    return CampoCartao.objects.none()
        
        # Filtros
        params = get_request_params(self.request)
        modelo_id = params.get('modelo_id')
        tipo = params.get('tipo')

        # Segurança extra: se for passado modelo_id, garantir que o modelo
        # pertence à empresa do usuário (empresa ou profissional). Caso
        # contrário retornamos vazio para evitar exposição indevida.
        if modelo_id:
            from .models import ModeloCartao as _ModeloCartao
            try:
                modelo = _ModeloCartao.objects.get(id=modelo_id)
            except _ModeloCartao.DoesNotExist:
                return CampoCartao.objects.none()

            # (debug prints removed)

            # Se o usuário for empresa, checar pertença
            if getattr(user, 'tipo_usuario', None) == 'empresa':
                from empresas.models import Empresa
                try:
                    empresa = Empresa.objects.get(usuario=user)
                    if modelo.empresa != empresa:
                        return CampoCartao.objects.none()
                except Empresa.DoesNotExist:
                    return CampoCartao.objects.none()

            # Se o usuário for profissional, checar pertença da empresa do prof
            if getattr(user, 'tipo_usuario', None) == 'profissional':
                from empresas.models import Profissional
                try:
                    prof = Profissional.objects.select_related('empresa').get(usuario=user)
                    if modelo.empresa != prof.empresa:
                        return CampoCartao.objects.none()
                except Profissional.DoesNotExist:
                    return CampoCartao.objects.none()

            queryset = queryset.filter(modelo_id=modelo_id)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset.order_by('ordem')
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def reorder(self, request):
        """Reordenar campos"""
        serializer = CampoCartaoReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        campos_ordem = serializer.validated_data['campos_ordem']
        
        for item in campos_ordem:
            campo_id = item['id']
            nova_ordem = item['ordem']
            CampoCartao.objects.filter(id=campo_id).update(ordem=nova_ordem)
        
        return Response({'message': 'Campos reordenados com sucesso.'})
    
    @action(detail=False, methods=['get'])
    def tipos_disponiveis(self, request):
        """Lista tipos de campo disponíveis"""
        tipos = TipoCampoSerializer.get_tipos_disponiveis()
        return Response(tipos)

