"""
Serializers for dashboard app
"""
from rest_framework import serializers
from .models import Dashboard, Relatorio, Estatistica, Alerta, TipoRelatorio, FormatoRelatorio


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer para Dashboard"""
    estatisticas = serializers.SerializerMethodField()
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'empresa', 'widgets_ativos', 'layout',
            'periodo_padrao', 'auto_refresh', 'refresh_interval',
            'estatisticas', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_estatisticas(self, obj):
        return obj.obter_estatisticas()


class DashboardConfigSerializer(serializers.Serializer):
    """Serializer para configuração do dashboard"""
    widgets_ativos = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    layout = serializers.DictField(required=False)
    periodo_padrao = serializers.IntegerField(min_value=1, max_value=365, required=False)
    auto_refresh = serializers.BooleanField(required=False)
    refresh_interval = serializers.IntegerField(min_value=30, max_value=3600, required=False)


class RelatorioSerializer(serializers.ModelSerializer):
    """Serializer para Relatorio"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gerado_por_nome = serializers.CharField(source='gerado_por.email', read_only=True)
    tamanho_mb = serializers.SerializerMethodField()
    esta_expirado = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Relatorio
        fields = [
            'id', 'empresa', 'gerado_por', 'gerado_por_nome',
            'tipo', 'tipo_display', 'formato', 'formato_display',
            'status', 'status_display', 'filtros', 'arquivo',
            'tamanho', 'tamanho_mb', 'iniciado_em', 'concluido_em',
            'erro', 'total_registros', 'created_at', 'expires_at', 'esta_expirado'
        ]
        read_only_fields = [
            'id', 'status', 'arquivo', 'tamanho', 'iniciado_em',
            'concluido_em', 'erro', 'total_registros', 'created_at',
            'expires_at', 'esta_expirado'
        ]
    
    def get_tamanho_mb(self, obj):
        if obj.tamanho > 0:
            return round(obj.tamanho / (1024 * 1024), 2)
        return 0


class RelatorioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de relatórios"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    formato_display = serializers.CharField(source='get_formato_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tamanho_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Relatorio
        fields = [
            'id', 'tipo', 'tipo_display', 'formato', 'formato_display',
            'status', 'status_display', 'tamanho_mb', 'created_at', 'expires_at'
        ]
    
    def get_tamanho_mb(self, obj):
        if obj.tamanho > 0:
            return round(obj.tamanho / (1024 * 1024), 2)
        return 0


class RelatorioCreateSerializer(serializers.Serializer):
    """Serializer para criação de relatório"""
    tipo = serializers.ChoiceField(choices=TipoRelatorio.choices)
    formato = serializers.ChoiceField(choices=FormatoRelatorio.choices)
    filtros = serializers.DictField(required=False, default=dict)
    
    # Filtros opcionais comuns
    data_inicio = serializers.DateField(required=False)
    data_fim = serializers.DateField(required=False)
    coleta_id = serializers.UUIDField(required=False)
    departamento_id = serializers.UUIDField(required=False)
    profissional_id = serializers.UUIDField(required=False)
    
    def validate(self, data):
        # Construir filtros baseado nos campos opcionais
        filtros = data.get('filtros', {})
        
        if 'data_inicio' in data:
            filtros['data_inicio'] = data.pop('data_inicio').isoformat()
        if 'data_fim' in data:
            filtros['data_fim'] = data.pop('data_fim').isoformat()
        if 'coleta_id' in data:
            filtros['coleta_id'] = str(data.pop('coleta_id'))
        if 'departamento_id' in data:
            filtros['departamento_id'] = str(data.pop('departamento_id'))
        if 'profissional_id' in data:
            filtros['profissional_id'] = str(data.pop('profissional_id'))
        
        data['filtros'] = filtros
        return data


class EstatisticaSerializer(serializers.ModelSerializer):
    """Serializer para Estatistica"""
    periodo_tipo_display = serializers.CharField(source='get_periodo_tipo_display', read_only=True)
    
    class Meta:
        model = Estatistica
        fields = [
            'id', 'empresa', 'data_referencia', 'periodo_tipo',
            'periodo_tipo_display', 'dados', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EstatisticaRangeSerializer(serializers.Serializer):
    """Serializer para buscar estatísticas por período"""
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()
    periodo_tipo = serializers.ChoiceField(
        choices=['dia', 'semana', 'mes', 'ano'],
        default='dia'
    )
    
    def validate(self, data):
        if data['data_inicio'] > data['data_fim']:
            raise serializers.ValidationError({
                'data_fim': 'Data fim deve ser posterior à data início.'
            })
        return data


class AlertaSerializer(serializers.ModelSerializer):
    """Serializer para Alerta"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    severidade_display = serializers.CharField(source='get_severidade_display', read_only=True)
    coleta_nome = serializers.CharField(source='coleta.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    
    class Meta:
        model = Alerta
        fields = [
            'id', 'empresa', 'tipo', 'tipo_display', 'severidade', 'severidade_display',
            'titulo', 'mensagem', 'coleta', 'coleta_nome',
            'profissional', 'profissional_nome', 'lido', 'resolvido', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AlertaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de alertas"""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    severidade_display = serializers.CharField(source='get_severidade_display', read_only=True)
    
    class Meta:
        model = Alerta
        fields = [
            'id', 'tipo', 'tipo_display', 'severidade', 'severidade_display',
            'titulo', 'lido', 'resolvido', 'created_at'
        ]


class DashboardWidgetSerializer(serializers.Serializer):
    """Serializer para adicionar/remover widgets"""
    widget_id = serializers.CharField()
    config = serializers.DictField(required=False, default=dict)


class DashboardEstatisticasGeraisSerializer(serializers.Serializer):
    """Serializer para estatísticas gerais do dashboard"""
    coletas = serializers.DictField()
    profissionais = serializers.DictField()
    modelos = serializers.DictField()
    departamentos = serializers.DictField()
    taxa_conclusao = serializers.FloatField()
    periodo_dias = serializers.IntegerField()
    alertas_nao_lidos = serializers.IntegerField()
    ultimas_atividades = serializers.ListField()
