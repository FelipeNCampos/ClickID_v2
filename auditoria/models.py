"""
Models do app auditoria - Sistema de Log de Ações
"""
import uuid
from django.db import models
from django.utils import timezone


class TipoAcao(models.TextChoices):
    """Tipos de ações auditáveis"""
    # Coletas
    COLETA_CRIADA = 'coleta_criada', 'Coleta Criada'
    COLETA_INICIADA = 'coleta_iniciada', 'Coleta Iniciada'
    COLETA_CANCELADA = 'coleta_cancelada', 'Coleta Cancelada'
    COLETA_CONCLUIDA = 'coleta_concluida', 'Coleta Concluída'
    COLETA_REABERTA = 'coleta_reaberta', 'Coleta Reaberta'
    
    # Participantes
    PARTICIPANTE_ADICIONADO = 'participante_adicionado', 'Participante Adicionado'
    PARTICIPANTE_REMOVIDO = 'participante_removido', 'Participante Removido'
    PARTICIPANTES_IMPORTADOS = 'participantes_importados', 'Participantes Importados'
    
    # Profissionais
    PROFISSIONAL_CRIADO = 'profissional_criado', 'Profissional Criado'
    PROFISSIONAL_EDITADO = 'profissional_editado', 'Profissional Editado'
    PROFISSIONAL_DESATIVADO = 'profissional_desativado', 'Profissional Desativado'
    PROFISSIONAL_REATIVADO = 'profissional_reativado', 'Profissional Reativado'
    
    # Outros
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    EXPORTACAO = 'exportacao', 'Exportação de Dados'


class LogAuditoria(models.Model):
    """
    Registro de auditoria de ações no sistema
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Quem fez a ação
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_auditoria'
    )
    usuario_nome = models.CharField('Nome do Usuário', max_length=255)
    usuario_email = models.EmailField('Email do Usuário')
    
    # O que foi feito
    tipo_acao = models.CharField(
        'Tipo de Ação',
        max_length=50,
        choices=TipoAcao.choices
    )
    descricao = models.TextField('Descrição')
    
    # Contexto
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_auditoria'
    )
    coleta = models.ForeignKey(
        'coletas.Coleta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_auditoria'
    )
    
    # Metadados
    dados_adicionais = models.JSONField('Dados Adicionais', null=True, blank=True)
    ip_address = models.GenericIPAddressField('Endereço IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    
    # Timestamp
    data_hora = models.DateTimeField('Data e Hora', default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['-data_hora', 'empresa']),
            models.Index(fields=['tipo_acao']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f'{self.usuario_nome} - {self.get_tipo_acao_display()} - {self.data_hora}'
    
    @classmethod
    def registrar(cls, usuario, tipo_acao, descricao, empresa=None, coleta=None, 
                  dados_adicionais=None, request=None):
        """
        Método helper para registrar uma ação
        """
        ip_address = None
        user_agent = ''
        
        if request:
            # Obter IP do request
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            usuario=usuario,
            usuario_nome=usuario.nome if hasattr(usuario, 'nome') else str(usuario),
            usuario_email=usuario.email,
            tipo_acao=tipo_acao,
            descricao=descricao,
            empresa=empresa,
            coleta=coleta,
            dados_adicionais=dados_adicionais,
            ip_address=ip_address,
            user_agent=user_agent
        )
