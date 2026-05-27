"""
Serializers for modelos app
"""
from rest_framework import serializers
from .models import ModeloCartao, CampoCartao, TipoCampo


class CampoCartaoSerializer(serializers.ModelSerializer):
    """Serializer para modelo CampoCartao"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    alinhamento_display = serializers.CharField(source='get_alinhamento_display', read_only=True)
    
    class Meta:
        model = CampoCartao
        fields = [
            'id', 'modelo', 'nome_campo', 'tipo', 'tipo_display',
            'obrigatorio', 'ordem', 'lado',
            # Configuração do formulário
            'pergunta_formulario', 'placeholder', 'texto_ajuda', 'opcoes', 'validacao_regex',
            # Posicionamento
            'posicao_x', 'posicao_y', 'largura', 'altura',
            # Estilo visual
            'fonte', 'tamanho_fonte', 'cor_texto', 'alinhamento', 'alinhamento_display',
            'negrito', 'italico', 'sublinhado', 'rotacao'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        # Validar se campo está dentro dos limites do cartão
        modelo = data.get('modelo')
        if modelo:
            posicao_x = data.get('posicao_x', 0)
            posicao_y = data.get('posicao_y', 0)
            largura = data.get('largura', 0)
            altura = data.get('altura', 0)
            
            if posicao_x + largura > modelo.largura_mm:
                raise serializers.ValidationError(
                    f'Campo ultrapassa largura do cartão ({modelo.largura_mm}mm)'
                )
            
            if posicao_y + altura > modelo.altura_mm:
                raise serializers.ValidationError(
                    f'Campo ultrapassa altura do cartão ({modelo.altura_mm}mm)'
                )
        
        return data
    
    def validate_opcoes(self, value):
        """Valida opções para campos de seleção"""
        tipo = self.initial_data.get('tipo')
        if tipo in ['selecao_unica', 'selecao_multipla']:
            if not value or not isinstance(value, list) or len(value) == 0:
                raise serializers.ValidationError(
                    'Campos de seleção devem ter pelo menos uma opção.'
                )
        return value


class CampoCartaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de campos"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = CampoCartao
        fields = [
            'id', 'nome_campo', 'tipo', 'tipo_display', 'lado',
            'obrigatorio', 'ordem', 'posicao_x', 'posicao_y',
            'largura', 'altura', 'fonte', 'tamanho_fonte', 'cor_texto',
            'alinhamento', 'negrito', 'italico', 'sublinhado',
            'pergunta_formulario', 'placeholder', 'texto_ajuda'
        ]


class ModeloCartaoSerializer(serializers.ModelSerializer):
    """Serializer para modelo ModeloCartao"""
    campos = CampoCartaoSerializer(many=True, read_only=True)
    total_campos = serializers.IntegerField(read_only=True)
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    
    class Meta:
        model = ModeloCartao
        fields = [
            'id', 'empresa', 'empresa_nome', 'nome', 'descricao',
            'largura_mm', 'altura_mm', 'dpi',
            'background_image', 'background_color',
            'background_image_verso', 'background_color_verso',
            'campos', 'total_campos', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_campos'] = instance.campos.count()
        return representation


class ModeloCartaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de modelos"""
    total_campos = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ModeloCartao
        fields = [
            'id', 'nome', 'descricao', 'largura_mm', 'altura_mm',
            'total_campos', 'is_active', 'created_at'
        ]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_campos'] = instance.campos.count()
        return representation


class ModeloCartaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de modelo com campos"""
    campos = CampoCartaoSerializer(many=True, required=False)
    
    class Meta:
        model = ModeloCartao
        fields = [
            'id', 'empresa', 'nome', 'descricao',
            'largura_mm', 'altura_mm', 'dpi',
            'background_image', 'background_color',
            'background_image_verso', 'background_color_verso',
            'campos', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validar que o modelo pertence à empresa correta"""
        user = self.context['request'].user
        empresa = data.get('empresa')
        
        # Empresas só podem criar modelos para si mesmas
        if user.tipo_usuario == 'empresa':
            from empresas.models import Empresa
            try:
                empresa_usuario = Empresa.objects.get(usuario=user)
                if empresa != empresa_usuario:
                    raise serializers.ValidationError(
                        'Você só pode criar modelos para sua própria empresa.'
                    )
            except Empresa.DoesNotExist:
                raise serializers.ValidationError('Empresa não encontrada.')
        
        # Validar nome único por empresa
        if ModeloCartao.objects.filter(empresa=empresa, nome=data.get('nome')).exists():
            raise serializers.ValidationError({
                'nome': 'Já existe um modelo com este nome para esta empresa.'
            })
        
        return data
    
    def create(self, validated_data):
        campos_data = validated_data.pop('campos', [])
        modelo = ModeloCartao.objects.create(**validated_data)
        
        for campo_data in campos_data:
            CampoCartao.objects.create(modelo=modelo, **campo_data)
        
        return modelo


class ModeloCartaoDuplicateSerializer(serializers.Serializer):
    """Serializer para duplicação de modelo"""
    novo_nome = serializers.CharField(max_length=255)
    copiar_campos = serializers.BooleanField(default=True)
    
    def validate_novo_nome(self, value):
        empresa = self.context['empresa']
        if ModeloCartao.objects.filter(empresa=empresa, nome=value).exists():
            raise serializers.ValidationError('Já existe um modelo com este nome.')
        return value


class CampoCartaoReorderSerializer(serializers.Serializer):
    """Serializer para reordenação de campos"""
    campos_ordem = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        allow_empty=False
    )

    def validate_campos_ordem(self, value):
        """Valida estrutura: [{'id': uuid, 'ordem': int}, ...]"""
        for item in value:
            if 'id' not in item or 'ordem' not in item:
                raise serializers.ValidationError(
                    'Cada item deve conter "id" e "ordem".'
                )
            # ordem deve ser um inteiro
            try:
                int(item['ordem'])
            except Exception:
                raise serializers.ValidationError('O campo "ordem" deve ser inteiro.')
        return value


class CanvasConfigSerializer(serializers.Serializer):
    """Serializer para configurações do canvas"""
    zoom = serializers.FloatField(min_value=0.1, max_value=5.0, default=1.0)
    grid_enabled = serializers.BooleanField(default=True)
    grid_size = serializers.IntegerField(min_value=1, max_value=50, default=5)
    snap_to_grid = serializers.BooleanField(default=True)
    show_rulers = serializers.BooleanField(default=True)
    background_visible = serializers.BooleanField(default=True)


class CampoCartaoPositionUpdateSerializer(serializers.Serializer):
    """Serializer para atualização de posição de campo"""
    posicao_x = serializers.DecimalField(max_digits=6, decimal_places=2)
    posicao_y = serializers.DecimalField(max_digits=6, decimal_places=2)
    largura = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    altura = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    
    def validate(self, data):
        modelo = self.context['modelo']
        posicao_x = data.get('posicao_x')
        posicao_y = data.get('posicao_y')
        largura = data.get('largura', 0)
        altura = data.get('altura', 0)
        
        if posicao_x + largura > modelo.largura_mm:
            raise serializers.ValidationError(
                f'Campo ultrapassa largura do cartão ({modelo.largura_mm}mm)'
            )
        
        if posicao_y + altura > modelo.altura_mm:
            raise serializers.ValidationError(
                f'Campo ultrapassa altura do cartão ({modelo.altura_mm}mm)'
            )
        
        return data


class TipoCampoSerializer(serializers.Serializer):
    """Serializer para listar tipos de campo disponíveis"""
    value = serializers.CharField()
    label = serializers.CharField()
    icon = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    
    @staticmethod
    def get_tipos_disponiveis():
        """Retorna lista de tipos de campo com metadados"""
        return [
            {
                'value': TipoCampo.TEXTO_CURTO,
                'label': 'Texto Curto',
                'icon': 'text',
                'description': 'Campo de texto com limite de caracteres'
            },
            {
                'value': TipoCampo.TEXTO_LONGO,
                'label': 'Texto Longo',
                'icon': 'paragraph',
                'description': 'Campo de texto multi-linha'
            },
            {
                'value': TipoCampo.EMAIL,
                'label': 'E-mail',
                'icon': 'email',
                'description': 'Campo de e-mail com validação'
            },
            {
                'value': TipoCampo.CPF,
                'label': 'CPF',
                'icon': 'id-card',
                'description': 'Campo de CPF com máscara e validação'
            },
            {
                'value': TipoCampo.TELEFONE,
                'label': 'Telefone',
                'icon': 'phone',
                'description': 'Campo de telefone com máscara'
            },
            {
                'value': TipoCampo.DATA,
                'label': 'Data',
                'icon': 'calendar',
                'description': 'Campo de data com seletor'
            },
            {
                'value': TipoCampo.NUMERO,
                'label': 'Número',
                'icon': 'number',
                'description': 'Campo numérico'
            },
            {
                'value': TipoCampo.FOTO,
                'label': 'Foto',
                'icon': 'camera',
                'description': 'Upload de foto do profissional'
            },
            {
                'value': TipoCampo.ASSINATURA,
                'label': 'Assinatura',
                'icon': 'signature',
                'description': 'Campo de assinatura digital'
            },
            {
                'value': TipoCampo.SELECAO_UNICA,
                'label': 'Seleção Única',
                'icon': 'radio',
                'description': 'Lista de opções com seleção única'
            },
            {
                'value': TipoCampo.SELECAO_MULTIPLA,
                'label': 'Seleção Múltipla',
                'icon': 'checkbox',
                'description': 'Lista de opções com múltipla escolha'
            },
            {
                'value': TipoCampo.CODIGO_BARRAS,
                'label': 'Código de Barras',
                'icon': 'barcode',
                'description': 'Geração de código de barras'
            },
            {
                'value': TipoCampo.QR_CODE,
                'label': 'QR Code',
                'icon': 'qrcode',
                'description': 'Geração de QR Code'
            },
            {
                'value': TipoCampo.IMAGEM_ESTATICA,
                'label': 'Imagem Estática',
                'icon': 'image',
                'description': 'Imagem fixa no cartão (logo, ícone)'
            },
        ]
