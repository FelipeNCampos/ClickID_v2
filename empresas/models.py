"""
Models do app empresas - Sistema ClickID
Gerenciamento de empresas, profissionais e departamentos
"""
import uuid
from django.db import models
from django.utils.text import slugify
from usuarios.models import Usuario


class Empresa(models.Model):
    """
    Empresa cliente com gestão de profissionais e coletas.
    Possui modelos de cartões privados e URL personalizada.
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='empresa_profile'
    )
    razao_social = models.CharField('Razão Social', max_length=255)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=255, blank=True)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    endereco = models.TextField('Endereço', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    logo = models.ImageField('Logo', upload_to='empresas/logos/', null=True, blank=True)
    url_personalizada = models.SlugField('URL Personalizada', max_length=100, unique=True)
    is_active = models.BooleanField('Ativa', default=True)
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    cadastrado_por = models.ForeignKey(
        'usuarios.Gerente',
        on_delete=models.SET_NULL,
        null=True,
        related_name='empresas_cadastradas'
    )
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['razao_social']
    
    def __str__(self):
        return f'{self.razao_social} - {self.cnpj}'
    
    def save(self, *args, **kwargs):
        if not self.url_personalizada:
            self.url_personalizada = slugify(self.nome_fantasia or self.razao_social)
        if self.usuario:
            self.usuario.tipo_usuario = Usuario.TIPO_EMPRESA
            self.usuario.save()
        super().save(*args, **kwargs)


class Departamento(models.Model):
    """
    Departamento para organização de profissionais dentro da empresa.
    Facilita coletas segmentadas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='departamentos'
    )
    nome = models.CharField('Nome do Departamento', max_length=255)
    descricao = models.TextField('Descrição', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        unique_together = ['empresa', 'nome']
        ordering = ['nome']
    
    def __str__(self):
        return f'{self.empresa.razao_social} - {self.nome}'
    
    def listar_profissionais(self):
        """Retorna todos os profissionais do departamento"""
        return self.profissionais.all()
    
    @property
    def total_profissionais(self):
        return self.profissionais.count()


class Profissional(models.Model):
    """
    Profissional vinculado a uma empresa.
    Preenche formulários e envia dados multimídia.
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profissional_profile'
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='profissionais'
    )
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profissionais'
    )
    nome = models.CharField('Nome Completo', max_length=255)
    cpf = models.CharField('CPF', max_length=14, unique=True)
    email = models.EmailField('E-mail', null=True, blank=True)
    dados_extras = models.JSONField('Dados Adicionais', default=dict, blank=True, help_text='Dados extras importados (CREA, RG, etc)')
    is_active = models.BooleanField('Ativo', default=True)
    senha_alterada = models.BooleanField('Senha Foi Alterada', default=False)
    data_primeiro_login = models.DateTimeField('Data do Primeiro Login', null=True, blank=True)
    cadastrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='profissionais_cadastrados'
    )
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['empresa', 'cpf']),
        ]
    
    def __str__(self):
        return f'{self.nome} - {self.cpf} ({self.empresa.razao_social})'
    
    def save(self, *args, **kwargs):
        if not self.usuario:
            raise ValueError('O campo `usuario` é obrigatório para Profissional.')
        super().save(*args, **kwargs)
    
    def gerar_senha_padrao(self):
        """Gera senha padrão: últimos 4 dígitos do CPF"""
        import re
        cpf_limpo = re.sub(r'[^0-9]', '', self.cpf)
        return cpf_limpo[-4:]
    
    def precisa_alterar_senha(self):
        """Verifica se profissional precisa alterar senha"""
        return not self.senha_alterada

