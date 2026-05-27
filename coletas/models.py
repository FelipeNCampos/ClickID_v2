"""
Models do app coletas - Sistema ClickID
Gerenciamento de coletas, respostas e mídias
"""
import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class StatusColeta(models.TextChoices):
    """Estados possíveis de uma coleta"""
    RASCUNHO = 'rascunho', 'Rascunho'
    EM_ANDAMENTO = 'em_andamento', 'Em Andamento'
    CONCLUIDA = 'concluida', 'Concluída'
    CANCELADA = 'cancelada', 'Cancelada'


class StatusPreenchimento(models.TextChoices):
    """Estados do preenchimento por profissional"""
    PENDENTE = 'pendente', 'Pendente'
    EM_PROGRESSO = 'em_progresso', 'Em Progresso'
    CONCLUIDO = 'concluido', 'Concluído'
    EXPIRADO = 'expirado', 'Expirado'


class Coleta(models.Model):
    """
    Coleta de dados com controle de status e progresso.
    Pode ser iniciada por Gerente ou Empresa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='coletas'
    )
    modelo = models.ForeignKey(
        'modelos.ModeloCartao',
        on_delete=models.PROTECT,
        related_name='coletas',
        null=True,
        blank=True
    )
    iniciado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='coletas_iniciadas'
    )
    
    nome = models.CharField('Nome da Coleta', max_length=255)
    descricao = models.TextField('Descrição', blank=True, null=True)
    tipo_coleta = models.CharField(
        'Tipo de Coleta',
        max_length=20,
        choices=[
            ('modelo_ativo', 'Modelo Ativo'),
            ('dados_extras', 'Dados Extras'),
        ],
        blank=True,
        null=True
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusColeta.choices,
        default=StatusColeta.RASCUNHO
    )
    
    # Configurações da coleta
    include_foto = models.BooleanField('Incluir Foto', default=True)
    include_assinatura = models.BooleanField('Incluir Assinatura', default=True)
    include_dados = models.BooleanField('Incluir Dados Textuais', default=True)
    
    # Datas
    data_inicio = models.DateTimeField('Data de Início', null=True, blank=True)
    data_fim = models.DateTimeField('Data de Término', null=True, blank=True)
    prazo = models.DateTimeField('Prazo', null=True, blank=True)
    
    # Estatísticas
    total_profissionais = models.IntegerField('Total de Profissionais', default=0)
    total_concluidos = models.IntegerField('Total Concluídos', default=0)
    
    # Controle
    is_active = models.BooleanField('Ativa', default=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Coleta'
        verbose_name_plural = 'Coletas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'{self.nome} - {self.empresa.razao_social} ({self.get_status_display()})'
    
    def calcular_percentual(self):
        """Calcula percentual de conclusão"""
        if self.total_profissionais == 0:
            return 0
        return round((self.total_concluidos / self.total_profissionais) * 100, 2)
    
    def adicionar_profissional(self, profissional):
        """Adiciona profissional à coleta"""
        coleta_prof, created = ColetaProfissional.objects.get_or_create(
            coleta=self,
            profissional=profissional,
            defaults={'status': StatusPreenchimento.PENDENTE}
        )
        if created:
            self.total_profissionais += 1
            self.save()
        return coleta_prof
    
    def remover_profissional(self, profissional):
        """Remove profissional da coleta"""
        ColetaProfissional.objects.filter(
            coleta=self,
            profissional=profissional
        ).delete()
        self.atualizar_totais()
    
    def cancelar(self):
        """Cancela a coleta"""
        self.status = StatusColeta.CANCELADA
        self.data_fim = timezone.now()
        self.save()
    
    def finalizar(self):
        """Finaliza a coleta"""
        self.status = StatusColeta.CONCLUIDA
        self.data_fim = timezone.now()
        self.save()
    
    def reabrir(self):
        """Reabre coleta cancelada ou concluída"""
        self.status = StatusColeta.EM_ANDAMENTO
        self.data_fim = None
        self.save()
    
    def atualizar_totais(self):
        """Recalcula totais de profissionais"""
        self.total_profissionais = self.coleta_profissionais.count()
        self.total_concluidos = self.coleta_profissionais.filter(
            status=StatusPreenchimento.CONCLUIDO
        ).count()
        self.save()
        
        # Auto-finalizar se todos concluíram
        if self.total_profissionais > 0 and self.total_profissionais == self.total_concluidos:
            if self.status == StatusColeta.EM_ANDAMENTO:
                self.finalizar()


class ColetaProfissional(models.Model):
    """
    Relacionamento Many-to-Many entre Coleta e Profissional.
    Controla status individual de preenchimento.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coleta = models.ForeignKey(
        Coleta,
        on_delete=models.CASCADE,
        related_name='coleta_profissionais'
    )
    profissional = models.ForeignKey(
        'empresas.Profissional',
        on_delete=models.CASCADE,
        related_name='coletas_atribuidas'
    )
    
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusPreenchimento.choices,
        default=StatusPreenchimento.PENDENTE
    )
    
    data_inicio = models.DateTimeField('Iniciado em', null=True, blank=True)
    data_conclusao = models.DateTimeField('Concluído em', null=True, blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Coleta do Profissional'
        verbose_name_plural = 'Coletas dos Profissionais'
        unique_together = ['coleta', 'profissional']
        ordering = ['coleta', 'profissional']
    
    def __str__(self):
        return f'{self.coleta.nome} - {self.profissional.nome} ({self.get_status_display()})'
    
    def iniciar(self):
        """Marca como em progresso"""
        if self.status == StatusPreenchimento.PENDENTE:
            self.status = StatusPreenchimento.EM_PROGRESSO
            self.data_inicio = timezone.now()
            self.save()
    
    def salvar_rascunho(self):
        """Salva progresso sem finalizar"""
        if self.status == StatusPreenchimento.PENDENTE:
            self.iniciar()
    
    def finalizar(self):
        """Finaliza preenchimento"""
        self.status = StatusPreenchimento.CONCLUIDO
        self.data_conclusao = timezone.now()
        self.save()
        # Atualizar totais da coleta
        self.coleta.atualizar_totais()
    
    def reenviar_notificacao(self):
        """Registra reenvio de notificação"""
        # TODO: Implementar com Celery task
        pass

    def gerar_token_acesso(self):
        """Gera um token de acesso temporário (64 hex chars)."""
        import secrets
        return secrets.token_hex(32)


class RespostaColeta(models.Model):
    """
    Container de todas as respostas de um profissional.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coleta_profissional = models.OneToOneField(
        ColetaProfissional,
        on_delete=models.CASCADE,
        related_name='resposta'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Resposta da Coleta'
        verbose_name_plural = 'Respostas das Coletas'
    
    def __str__(self):
        return f'Resposta de {self.coleta_profissional.profissional.nome}'
    
    def validar(self):
        """Valida se todos os campos obrigatórios foram preenchidos"""
        modelo = self.coleta_profissional.coleta.modelo
        campos_obrigatorios = modelo.campos.filter(obrigatorio=True)
        
        for campo in campos_obrigatorios:
            if campo.tipo == 'foto':
                if not hasattr(self, 'foto'):
                    return False, f'Foto obrigatória não enviada'
            elif campo.tipo == 'assinatura':
                if not hasattr(self, 'assinatura'):
                    return False, f'Assinatura obrigatória não enviada'
            else:
                if not self.respostas_campos.filter(campo=campo).exists():
                    return False, f'Campo obrigatório não preenchido: {campo.nome_campo}'
        
        return True, 'OK'


class RespostaCampo(models.Model):
    """
    Resposta individual de um campo do formulário.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resposta_coleta = models.ForeignKey(
        RespostaColeta,
        on_delete=models.CASCADE,
        related_name='respostas_campos'
    )
    campo = models.ForeignKey(
        'modelos.CampoCartao',
        on_delete=models.PROTECT,
        related_name='respostas'
    )
    
    # Valores possíveis (usar o apropriado baseado no tipo)
    valor_texto = models.TextField('Valor Texto', blank=True)
    valor_numero = models.DecimalField(
        'Valor Número',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    valor_data = models.DateField('Valor Data', null=True, blank=True)
    valor_json = models.JSONField('Valor JSON', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Resposta de Campo'
        verbose_name_plural = 'Respostas de Campos'
        unique_together = ['resposta_coleta', 'campo']
    
    def __str__(self):
        return f'{self.campo.nome_campo}: {self.obter_valor()}'
    
    def obter_valor(self):
        """Retorna valor apropriado baseado no tipo do campo"""
        if self.campo.tipo in ['numero']:
            return self.valor_numero
        elif self.campo.tipo == 'data':
            return self.valor_data
        elif self.campo.tipo in ['selecao_multipla']:
            return self.valor_json
        else:
            return self.valor_texto
    
    def validar(self):
        """Valida valor conforme tipo do campo"""
        # TODO: Implementar validações específicas por tipo
        if self.campo.obrigatorio and not self.obter_valor():
            return False
        return True


class Foto(models.Model):
    """
    Foto enviada pelo profissional.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resposta_coleta = models.OneToOneField(
        RespostaColeta,
        on_delete=models.CASCADE,
        related_name='foto'
    )
    arquivo = models.ImageField(
        'Foto',
        upload_to='coletas/fotos/%Y/%m/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    tamanho = models.IntegerField('Tamanho (bytes)', default=0)
    formato = models.CharField('Formato', max_length=10)
    resolucao = models.CharField('Resolução', max_length=20, blank=True)
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'
    
    def __str__(self):
        return f'Foto de {self.resposta_coleta.coleta_profissional.profissional.nome}'
    
    def validar_formato(self):
        """Valida se formato é aceito"""
        return self.formato.lower() in ['jpg', 'jpeg', 'png']
    
    def validar_tamanho(self, max_mb=5):
        """Valida tamanho máximo"""
        max_bytes = max_mb * 1024 * 1024
        return self.tamanho <= max_bytes
    
    def gerar_thumbnail(self):
        """Gera miniatura da foto"""
        # TODO: Implementar com Pillow
        pass


class Assinatura(models.Model):
    """
    Assinatura digital do profissional.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resposta_coleta = models.OneToOneField(
        RespostaColeta,
        on_delete=models.CASCADE,
        related_name='assinatura'
    )
    arquivo = models.ImageField(
        'Assinatura',
        upload_to='coletas/assinaturas/%Y/%m/',
        validators=[FileExtensionValidator(['png'])]
    )
    tamanho = models.IntegerField('Tamanho (bytes)', default=0)
    formato = models.CharField('Formato', max_length=10, default='png')
    uploaded_at = models.DateTimeField('Enviado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
    
    def __str__(self):
        return f'Assinatura de {self.resposta_coleta.coleta_profissional.profissional.nome}'
    
    def validar_complexidade(self):
        """Valida se assinatura tem complexidade mínima"""
        # TODO: Implementar análise de complexidade da imagem
        return True
    
    def converter_png(self):
        """Converte para PNG com fundo transparente"""
        # TODO: Implementar com Pillow
        pass


class TipoNotificacao(models.TextChoices):
    """Tipos de notificações"""
    COLETA_INICIADA = 'coleta_iniciada', 'Coleta Iniciada'
    LEMBRETE_PENDENCIA = 'lembrete_pendencia', 'Lembrete de Pendência'
    COLETA_CONCLUIDA = 'coleta_concluida', 'Coleta Concluída'
    SENHA_ALTERADA = 'senha_alterada', 'Senha Alterada'
    CADASTRO_PROFISSIONAL = 'cadastro_profissional', 'Cadastro de Profissional'
    RECUPERACAO_SENHA = 'recuperacao_senha', 'Recuperação de Senha'


class Notificacao(models.Model):
    """
    Notificações por email para profissionais.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinatario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    tipo = models.CharField(
        'Tipo',
        max_length=30,
        choices=TipoNotificacao.choices
    )
    assunto = models.CharField('Assunto', max_length=255)
    mensagem = models.TextField('Mensagem')
    enviado_em = models.DateTimeField('Enviado em', null=True, blank=True)
    lido = models.BooleanField('Lido', default=False)
    tentativas_envio = models.IntegerField('Tentativas de Envio', default=0)
    
    # Relacionamento opcional com coleta
    coleta_profissional = models.ForeignKey(
        ColetaProfissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notificacoes'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_tipo_display()} - {self.destinatario.email}'
    
    def enviar(self):
        """Envia notificação por email"""
        # TODO: Implementar com Celery task
        self.tentativas_envio += 1
        self.enviado_em = timezone.now()
        self.save()
        return True
    
    def marcar_lido(self):
        """Marca notificação como lida"""
        self.lido = True
        self.save()
    
    def reenviar(self):
        """Reenvia notificação"""
        if self.tentativas_envio < 5:  # Limite de reenvios
            return self.enviar()
        return False


class LogEmail(models.Model):
    """
    Log de envio de emails.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notificacao = models.ForeignKey(
        Notificacao,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_envio'
    )
    destinatario = models.EmailField('Destinatário')
    assunto = models.CharField('Assunto', max_length=255)
    enviado_em = models.DateTimeField('Enviado em', auto_now_add=True)
    status = models.CharField(
        'Status',
        max_length=20,
        choices=[
            ('sucesso', 'Sucesso'),
            ('erro', 'Erro'),
            ('pendente', 'Pendente'),
        ],
        default='pendente'
    )
    erro = models.TextField('Erro', blank=True)
    
    class Meta:
        verbose_name = 'Log de Email'
        verbose_name_plural = 'Logs de Emails'
        ordering = ['-enviado_em']
    
    def __str__(self):
        return f'{self.destinatario} - {self.status}'
    
    @classmethod
    def registrar_envio(cls, notificacao, destinatario, assunto):
        """Registra envio bem-sucedido"""
        return cls.objects.create(
            notificacao=notificacao,
            destinatario=destinatario,
            assunto=assunto,
            status='sucesso'
        )
    
    @classmethod
    def registrar_erro(cls, notificacao, destinatario, assunto, erro):
        """Registra erro no envio"""
        return cls.objects.create(
            notificacao=notificacao,
            destinatario=destinatario,
            assunto=assunto,
            status='erro',
            erro=str(erro)
        )

