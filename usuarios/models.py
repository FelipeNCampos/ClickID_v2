"""
Models do app usuarios - Sistema ClickID
Baseado no diagrama UML de classes
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def validate_cpf(value):
    """Validador simples de CPF"""
    import re
    cpf = re.sub(r'[^0-9]', '', value)
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos')
    # Adicionar validação completa de dígitos verificadores aqui
    return value


class UsuarioManager(BaseUserManager):
    """Manager customizado para o modelo Usuario"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo abstrato base para todos os usuários do sistema.
    Implementa autenticação JWT e controle de acesso.
    """
    TIPO_GERENTE = 'gerente'
    TIPO_EMPRESA = 'empresa'
    TIPO_PROFISSIONAL = 'profissional'
    
    TIPOS_USUARIO = [
        (TIPO_GERENTE, 'Gerente'),
        (TIPO_EMPRESA, 'Empresa'),
        (TIPO_PROFISSIONAL, 'Profissional'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('E-mail', unique=True, validators=[validate_email])
    tipo_usuario = models.CharField('Tipo de Usuário', max_length=20, choices=TIPOS_USUARIO)
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Staff', default=False)
    last_login = models.DateTimeField('Último Login', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.email} ({self.get_tipo_usuario_display()})'
    
    def get_full_name(self):
        return self.email
    
    def get_short_name(self):
        return self.email


class Gerente(models.Model):
    """
    Gerente do sistema com permissões administrativas.
    Pode cadastrar empresas, gerentes e gerenciar modelos.
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='gerente_profile'
    )
    nome = models.CharField('Nome Completo', max_length=255)
    cpf = models.CharField('CPF', max_length=14, unique=True, validators=[validate_cpf])
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    
    class Meta:
        verbose_name = 'Gerente'
        verbose_name_plural = 'Gerentes'
    
    def __str__(self):
        return f'{self.nome} - {self.cpf}'
    
    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario.tipo_usuario = Usuario.TIPO_GERENTE
            self.usuario.save()
        super().save(*args, **kwargs)


class LogAuditoria(models.Model):
    """
    Log completo de todas as ações no sistema para auditoria.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs'
    )
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True, db_index=True)
    usuario_tipo = models.CharField('Tipo de Usuário', max_length=20)
    acao = models.CharField('Ação', max_length=255)
    descricao = models.TextField('Descrição', blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    dados_alterados = models.JSONField('Dados Alterados', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'usuario']),
            models.Index(fields=['acao']),
        ]
    
    def __str__(self):
        return f'{self.timestamp} - {self.acao} - {self.usuario}'
    
    @classmethod
    def registrar(cls, usuario, acao, descricao='', ip_address=None, user_agent='', dados=None):
        """Método helper para registrar ações"""
        return cls.objects.create(
            usuario=usuario,
            usuario_tipo=usuario.tipo_usuario if usuario else '',
            acao=acao,
            descricao=descricao,
            ip_address=ip_address,
            user_agent=user_agent,
            dados_alterados=dados
        )

