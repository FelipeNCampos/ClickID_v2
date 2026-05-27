"""
Serializers for coletas app
"""
from rest_framework import serializers
from .models import (
    Coleta, ColetaProfissional, RespostaColeta, RespostaCampo,
    Foto, Assinatura, Notificacao, LogEmail,
    StatusColeta, StatusPreenchimento, TipoNotificacao
)
from empresas.models import Profissional
from empresas.serializers import ProfissionalListSerializer


class ColetaProfissionalSerializer(serializers.ModelSerializer):
    """Serializer para ColetaProfissional"""
    profissional = ProfissionalListSerializer(read_only=True)
    profissional_id = serializers.UUIDField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    coleta_nome = serializers.CharField(source='coleta.nome', read_only=True)
    data_resposta = serializers.DateTimeField(source='data_conclusao', read_only=True)
    
    class Meta:
        model = ColetaProfissional
        fields = [
            'id', 'coleta', 'profissional', 'profissional_id',
            'status', 'status_display', 'coleta_nome', 'data_inicio', 'data_conclusao', 'data_resposta', 'ip_address'
        ]
        read_only_fields = ['id', 'data_inicio', 'data_conclusao', 'ip_address']


class ColetaSerializer(serializers.ModelSerializer):
    """Serializer para Coleta"""
    coleta_profissionais = ColetaProfissionalSerializer(many=True, read_only=True)
    profissionais_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()
    empresa_nome = serializers.SerializerMethodField()
    empresa_razao_social = serializers.SerializerMethodField()
    modelo_nome = serializers.CharField(source='modelo.nome', read_only=True)
    criado_em = serializers.DateTimeField(source='created_at', read_only=True)
    data_conclusao = serializers.DateTimeField(source='data_fim', read_only=True)
    
    class Meta:
        model = Coleta
        fields = [
            'id', 'empresa', 'empresa_nome', 'empresa_razao_social', 'modelo', 'modelo_nome',
            'iniciado_por', 'nome', 'descricao', 'tipo_coleta', 'status', 'status_display',
            'include_foto', 'include_assinatura', 'include_dados',
            'data_inicio', 'data_fim', 'data_conclusao', 'prazo',
            'total_profissionais', 'total_concluidos', 'percentual_conclusao',
            'coleta_profissionais', 'profissionais_ids', 'is_active',
            'created_at', 'criado_em', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_profissionais', 'total_concluidos',
            'created_at', 'updated_at'
        ]
    
    def get_percentual_conclusao(self, obj):
        return obj.calcular_percentual()
    
    def get_empresa_nome(self, obj):
        """Retorna nome fantasia da empresa ou razão social como fallback"""
        if obj.empresa:
            return obj.empresa.nome_fantasia if obj.empresa.nome_fantasia else obj.empresa.razao_social
        return 'Empresa não identificada'
    
    def get_empresa_razao_social(self, obj):
        """Retorna razão social da empresa"""
        if obj.empresa:
            return obj.empresa.razao_social
        return 'Empresa não identificada'
    
    def to_representation(self, instance):
        """Customizar representação dos dados"""
        data = super().to_representation(instance)
        return data
    
    def create(self, validated_data):
        profissionais_ids = validated_data.pop('profissionais_ids', [])
        coleta = Coleta.objects.create(**validated_data)
        
        # Adicionar profissionais à coleta
        for prof_id in profissionais_ids:
            try:
                profissional = Profissional.objects.get(usuario=prof_id)
                coleta.adicionar_profissional(profissional)
            except Profissional.DoesNotExist:
                pass
        
        # Atualizar status para em_andamento se profissionais foram adicionados
        if profissionais_ids and coleta.status == StatusColeta.RASCUNHO:
            from django.utils import timezone
            coleta.status = StatusColeta.EM_ANDAMENTO
            coleta.data_inicio = timezone.now()
            coleta.save()
        
        return coleta


class ColetaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de coletas"""
    data_inicio = serializers.DateTimeField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    percentual_conclusao = serializers.SerializerMethodField()
    empresa_nome = serializers.SerializerMethodField()
    empresa_razao_social = serializers.SerializerMethodField()
    modelo_nome = serializers.CharField(source='modelo.nome', read_only=True)
    criado_em = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Coleta
        fields = [
            'id', 'nome', 'empresa_nome', 'empresa_razao_social', 'modelo_nome', 
            'data_inicio',
            'status', 'status_display', 'descricao',
            'total_profissionais', 'total_concluidos', 'percentual_conclusao',
            'prazo', 'created_at', 'criado_em'
        ]
    
    def get_percentual_conclusao(self, obj):
        return obj.calcular_percentual()
    
    def get_empresa_nome(self, obj):
        """Retorna nome fantasia da empresa ou razão social como fallback"""
        if obj.empresa:
            return obj.empresa.nome_fantasia if obj.empresa.nome_fantasia else obj.empresa.razao_social
        return 'Empresa não identificada'
    
    def get_empresa_razao_social(self, obj):
        """Retorna razão social da empresa"""
        if obj.empresa:
            return obj.empresa.razao_social
        return 'Empresa não identificada'


class RespostaCampoSerializer(serializers.ModelSerializer):
    """Serializer para RespostaCampo"""
    campo_nome = serializers.CharField(source='campo.nome_campo', read_only=True)
    campo_tipo = serializers.CharField(source='campo.tipo', read_only=True)
    valor = serializers.SerializerMethodField()
    
    class Meta:
        model = RespostaCampo
        fields = [
            'id', 'resposta_coleta', 'campo', 'campo_nome', 'campo_tipo',
            'valor_texto', 'valor_numero', 'valor_data', 'valor_json', 'valor'
        ]
        read_only_fields = ['id']
    
    def get_valor(self, obj):
        return obj.obter_valor()


class FotoSerializer(serializers.ModelSerializer):
    """Serializer para Foto"""
    class Meta:
        model = Foto
        fields = [
            'id', 'resposta_coleta', 'arquivo', 'tamanho',
            'formato', 'resolucao', 'uploaded_at'
        ]
        read_only_fields = ['id', 'tamanho', 'formato', 'resolucao', 'uploaded_at']


class AssinaturaSerializer(serializers.ModelSerializer):
    """Serializer para Assinatura"""
    class Meta:
        model = Assinatura
        fields = [
            'id', 'resposta_coleta', 'arquivo', 'tamanho',
            'formato', 'uploaded_at'
        ]
        read_only_fields = ['id', 'tamanho', 'formato', 'uploaded_at']


class RespostaColetaSerializer(serializers.ModelSerializer):
    """Serializer para RespostaColeta"""
    respostas_campos = RespostaCampoSerializer(many=True, read_only=True)
    foto = FotoSerializer(read_only=True)
    assinatura = AssinaturaSerializer(read_only=True)
    profissional_nome = serializers.CharField(
        source='coleta_profissional.profissional.nome',
        read_only=True
    )
    
    class Meta:
        model = RespostaColeta
        fields = [
            'id', 'coleta_profissional', 'profissional_nome',
            'respostas_campos', 'foto', 'assinatura',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RespostaColetaCreateSerializer(serializers.Serializer):
    """Serializer para criação de resposta com todos os dados"""
    coleta_profissional_id = serializers.UUIDField()
    respostas = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    foto = serializers.ImageField(required=False, allow_null=True)
    assinatura = serializers.ImageField(required=False, allow_null=True)
    
    def validate_coleta_profissional_id(self, value):
        try:
            ColetaProfissional.objects.get(id=value)
        except ColetaProfissional.DoesNotExist:
            raise serializers.ValidationError('Coleta profissional não encontrada.')
        return value
    
    def validate_respostas(self, value):
        """Valida estrutura das respostas"""
        for resposta in value:
            if 'campo_id' not in resposta:
                raise serializers.ValidationError('Cada resposta deve ter campo_id.')
        return value
    
    def create(self, validated_data):
        from modelos.models import CampoCartao
        
        coleta_prof_id = validated_data['coleta_profissional_id']
        respostas_data = validated_data.get('respostas', [])
        foto_file = validated_data.get('foto')
        assinatura_file = validated_data.get('assinatura')
        
        # Buscar ou criar RespostaColeta
        coleta_prof = ColetaProfissional.objects.get(id=coleta_prof_id)
        resposta_coleta, created = RespostaColeta.objects.get_or_create(
            coleta_profissional=coleta_prof
        )
        
        # Criar respostas dos campos
        for resposta_data in respostas_data:
            campo_id = resposta_data.get('campo_id')
            campo = CampoCartao.objects.get(id=campo_id)
            
            # Determinar qual campo de valor usar
            campo_valor = {}
            if campo.tipo in ['numero']:
                campo_valor['valor_numero'] = resposta_data.get('valor')
            elif campo.tipo == 'data':
                campo_valor['valor_data'] = resposta_data.get('valor')
            elif campo.tipo in ['selecao_multipla']:
                campo_valor['valor_json'] = resposta_data.get('valor')
            else:
                campo_valor['valor_texto'] = resposta_data.get('valor')
            
            RespostaCampo.objects.update_or_create(
                resposta_coleta=resposta_coleta,
                campo=campo,
                defaults=campo_valor
            )
        
        # Criar/atualizar foto
        if foto_file:
            Foto.objects.update_or_create(
                resposta_coleta=resposta_coleta,
                defaults={
                    'arquivo': foto_file,
                    'tamanho': foto_file.size,
                    'formato': foto_file.name.split('.')[-1]
                }
            )
        
        # Criar/atualizar assinatura
        if assinatura_file:
            Assinatura.objects.update_or_create(
                resposta_coleta=resposta_coleta,
                defaults={
                    'arquivo': assinatura_file,
                    'tamanho': assinatura_file.size,
                    'formato': 'png'
                }
            )
        
        return resposta_coleta


class NotificacaoSerializer(serializers.ModelSerializer):
    """Serializer para Notificacao"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    destinatario_email = serializers.CharField(source='destinatario.email', read_only=True)
    
    class Meta:
        model = Notificacao
        fields = [
            'id', 'destinatario', 'destinatario_email', 'tipo', 'tipo_display',
            'assunto', 'mensagem', 'enviado_em', 'lido', 'tentativas_envio',
            'coleta_profissional', 'created_at'
        ]
        read_only_fields = [
            'id', 'enviado_em', 'tentativas_envio', 'created_at'
        ]


class LogEmailSerializer(serializers.ModelSerializer):
    """Serializer para LogEmail"""
    class Meta:
        model = LogEmail
        fields = [
            'id', 'notificacao', 'destinatario', 'assunto',
            'enviado_em', 'status', 'erro'
        ]
        read_only_fields = fields


class ColetaIniciarSerializer(serializers.Serializer):
    """Serializer para iniciar coleta"""
    profissionais_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    departamentos_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    todos_profissionais = serializers.BooleanField(default=False)
    enviar_notificacao = serializers.BooleanField(default=True)
    
    def validate(self, data):
        if not data.get('todos_profissionais') and not data.get('profissionais_ids') and not data.get('departamentos_ids'):
            raise serializers.ValidationError(
                'Informe profissionais_ids, departamentos_ids ou marque todos_profissionais.'
            )
        return data


class ColetaImportExcelSerializer(serializers.Serializer):
    """Serializer para importação de profissionais via Excel"""
    arquivo = serializers.FileField()
    enviar_notificacao = serializers.BooleanField(default=True)
    
    def validate_arquivo(self, value):
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                'Formato inválido. Use Excel (.xlsx ou .xls).'
            )
        
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            raise serializers.ValidationError('Arquivo muito grande. Máximo: 5 MB.')
        
        return value


class ColetaEstatisticasSerializer(serializers.Serializer):
    """Serializer para estatísticas da coleta"""
    total_profissionais = serializers.IntegerField()
    total_concluidos = serializers.IntegerField()
    total_pendentes = serializers.IntegerField()
    total_em_progresso = serializers.IntegerField()
    percentual_conclusao = serializers.FloatField()
    tempo_medio_conclusao = serializers.DurationField(required=False, allow_null=True)
    profissionais_por_status = serializers.DictField()
    
    # Aliases para compatibilidade (não usar source em Serializer)
    participantes_concluidos = serializers.IntegerField()
    participantes_pendentes = serializers.IntegerField()
    participantes_em_progresso = serializers.IntegerField()
