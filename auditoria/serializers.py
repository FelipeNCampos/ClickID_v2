"""
Serializers for auditoria app
"""
from rest_framework import serializers
from .models import LogAuditoria


class LogAuditoriaSerializer(serializers.ModelSerializer):
    """Serializer para LogAuditoria"""
    tipo_acao_display = serializers.CharField(source='get_tipo_acao_display', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    coleta_nome = serializers.CharField(source='coleta.nome', read_only=True)
    
    class Meta:
        model = LogAuditoria
        fields = [
            'id', 'usuario_nome', 'usuario_email', 'tipo_acao', 'tipo_acao_display',
            'descricao', 'empresa', 'empresa_nome', 'coleta', 'coleta_nome',
            'dados_adicionais', 'ip_address', 'data_hora'
        ]
        read_only_fields = fields
