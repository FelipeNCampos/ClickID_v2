"""
Models do app dashboard - Sistema ClickID
Gerenciamento de dashboards, relatórios e estatísticas
"""
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


class TipoRelatorio(models.TextChoices):
    """Tipos de relatórios"""
    COLETAS_GERAL = 'coletas_geral', 'Relatório Geral de Coletas'
    COLETAS_DETALHADO = 'coletas_detalhado', 'Relatório Detalhado de Coletas'
    PROFISSIONAIS = 'profissionais', 'Relatório de Profissionais'
    AUDITORIA = 'auditoria', 'Relatório de Auditoria'
    PENDENCIAS = 'pendencias', 'Relatório de Pendências'
    CONCLUSAO = 'conclusao', 'Relatório de Conclusão'
    DEPARTAMENTOS = 'departamentos', 'Relatório por Departamentos'


class FormatoRelatorio(models.TextChoices):
    """Formatos de exportação de relatórios"""
    PDF = 'pdf', 'PDF'
    EXCEL = 'excel', 'Excel'
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'


class StatusRelatorio(models.TextChoices):
    """Status de geração de relatório"""
    PENDENTE = 'pendente', 'Pendente'
    PROCESSANDO = 'processando', 'Processando'
    CONCLUIDO = 'concluido', 'Concluído'
    ERRO = 'erro', 'Erro'


class Dashboard(models.Model):
    """
    Dashboard customizável por empresa.
    Armazena configurações de visualização.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.OneToOneField(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='dashboard'
    )
    
    # Configurações de visualização
    widgets_ativos = models.JSONField(
        'Widgets Ativos',
        default=list,
        help_text='Lista de widgets habilitados no dashboard'
    )
    layout = models.JSONField(
        'Layout',
        default=dict,
        help_text='Configuração de posicionamento dos widgets'
    )
    
    # Preferências
    periodo_padrao = models.IntegerField(
        'Período Padrão (dias)',
        default=30,
        help_text='Período padrão para exibição de estatísticas'
    )
    auto_refresh = models.BooleanField('Auto-atualização', default=True)
    refresh_interval = models.IntegerField(
        'Intervalo de Atualização (segundos)',
        default=300
    )
    
    # Novos campos
    nome = models.CharField(
        'Nome',
        max_length=255,
        help_text='Nome do dashboard'
    )
    descricao = models.TextField(
        'Descrição',
        blank=True,
        help_text='Descrição do dashboard'
    )
    widgets = models.JSONField(
        'Widgets',
        default=list,
        help_text='Configuração de widgets'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
    
    def __str__(self):
        return f'Dashboard - {self.empresa.razao_social}'
    
    def obter_estatisticas(self):
        """Retorna estatísticas consolidadas da empresa"""
        empresa = self.empresa
        periodo = timezone.now() - timedelta(days=self.periodo_padrao)
        
        from coletas.models import Coleta, StatusColeta, StatusPreenchimento
        
        # Estatísticas de coletas
        coletas_total = empresa.coletas.count()
        coletas_ativas = empresa.coletas.filter(
            status=StatusColeta.EM_ANDAMENTO
        ).count()
        coletas_concluidas = empresa.coletas.filter(
            status=StatusColeta.CONCLUIDA
        ).count()
        coletas_periodo = empresa.coletas.filter(
            created_at__gte=periodo
        ).count()
        
        # Estatísticas de profissionais
        profissionais_total = empresa.profissionais.count()
        profissionais_ativos = empresa.profissionais.filter(
            is_active=True
        ).count()
        
        # Estatísticas de modelos
        modelos_total = empresa.modelos.count()
        modelos_ativos = empresa.modelos.filter(is_active=True).count()
        
        # Estatísticas de departamentos
        departamentos_total = empresa.departamentos.count()
        
        # Taxa de conclusão
        from coletas.models import ColetaProfissional
        total_atribuicoes = ColetaProfissional.objects.filter(
            coleta__empresa=empresa
        ).count()
        total_concluidas_atribuicoes = ColetaProfissional.objects.filter(
            coleta__empresa=empresa,
            status=StatusPreenchimento.CONCLUIDO
        ).count()
        
        taxa_conclusao = 0
        if total_atribuicoes > 0:
            taxa_conclusao = round(
                (total_concluidas_atribuicoes / total_atribuicoes) * 100,
                2
            )
        
        return {
            'coletas': {
                'total': coletas_total,
                'ativas': coletas_ativas,
                'concluidas': coletas_concluidas,
                'periodo': coletas_periodo,
            },
            'profissionais': {
                'total': profissionais_total,
                'ativos': profissionais_ativos,
            },
            'modelos': {
                'total': modelos_total,
                'ativos': modelos_ativos,
            },
            'departamentos': {
                'total': departamentos_total,
            },
            'taxa_conclusao': taxa_conclusao,
            'periodo_dias': self.periodo_padrao,
        }
    
    def adicionar_widget(self, widget_id, config=None):
        """Adiciona widget ao dashboard"""
        if widget_id not in self.widgets_ativos:
            self.widgets_ativos.append(widget_id)
            if config and isinstance(self.layout, dict):
                self.layout[widget_id] = config
            self.save()
    
    def remover_widget(self, widget_id):
        """Remove widget do dashboard"""
        if widget_id in self.widgets_ativos:
            self.widgets_ativos.remove(widget_id)
            if isinstance(self.layout, dict) and widget_id in self.layout:
                del self.layout[widget_id]
            self.save()
    
    def resetar_layout(self):
        """Reseta layout para configuração padrão"""
        self.widgets_ativos = [
            'coletas_ativas',
            'profissionais_ativos',
            'taxa_conclusao',
            'grafico_coletas',
            'ultimas_atividades',
        ]
        self.layout = {}
        self.save()


class Relatorio(models.Model):
    """
    Relatórios gerados sob demanda.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='relatorios'
    )
    gerado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='relatorios_gerados'
    )
    
    tipo = models.CharField(
        'Tipo',
        max_length=30,
        choices=TipoRelatorio.choices
    )
    formato = models.CharField(
        'Formato',
        max_length=10,
        choices=FormatoRelatorio.choices,
        default=FormatoRelatorio.PDF
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusRelatorio.choices,
        default=StatusRelatorio.PENDENTE
    )
    
    # Filtros aplicados (JSON)
    filtros = models.JSONField('Filtros', default=dict)
    
    # Arquivo gerado
    arquivo = models.FileField(
        'Arquivo',
        upload_to='relatorios/%Y/%m/',
        null=True,
        blank=True
    )
    tamanho = models.IntegerField('Tamanho (bytes)', default=0)
    
    # Controle de processamento
    iniciado_em = models.DateTimeField('Iniciado em', null=True, blank=True)
    concluido_em = models.DateTimeField('Concluído em', null=True, blank=True)
    erro = models.TextField('Erro', blank=True)
    
    # Estatísticas do relatório
    total_registros = models.IntegerField('Total de Registros', default=0)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    expires_at = models.DateTimeField('Expira em', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Relatório'
        verbose_name_plural = 'Relatórios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_tipo_display()} - {self.empresa.razao_social} ({self.get_status_display()})'
    
    def save(self, *args, **kwargs):
        # Define data de expiração (30 dias)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    def gerar(self):
        """Dispara geração do relatório (Celery task)"""
        self.status = StatusRelatorio.PROCESSANDO
        self.iniciado_em = timezone.now()
        self.save()
        # TODO: Chamar Celery task
        # from dashboard.tasks import gerar_relatorio_task
        # gerar_relatorio_task.delay(self.id)
    
    def marcar_concluido(self):
        """Marca relatório como concluído"""
        self.status = StatusRelatorio.CONCLUIDO
        self.concluido_em = timezone.now()
        self.save()
    
    def marcar_erro(self, mensagem_erro):
        """Marca relatório com erro"""
        self.status = StatusRelatorio.ERRO
        self.erro = mensagem_erro
        self.concluido_em = timezone.now()
        self.save()
    
    def esta_expirado(self):
        """Verifica se relatório está expirado"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def renovar_expiracao(self, dias=30):
        """Renova período de expiração"""
        self.expires_at = timezone.now() + timedelta(days=dias)
        self.save()
    
    @classmethod
    def limpar_expirados(cls):
        """Remove relatórios expirados"""
        expirados = cls.objects.filter(expires_at__lt=timezone.now())
        count = expirados.count()
        # Deletar arquivos antes
        for relatorio in expirados:
            if relatorio.arquivo:
                relatorio.arquivo.delete()
        expirados.delete()
        return count


class Estatistica(models.Model):
    """
    Cache de estatísticas calculadas periodicamente.
    Atualizado por Celery task a cada X minutos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='estatisticas'
    )
    
    # Período de referência
    data_referencia = models.DateField('Data de Referência')
    periodo_tipo = models.CharField(
        'Tipo de Período',
        max_length=20,
        choices=[
            ('dia', 'Diário'),
            ('semana', 'Semanal'),
            ('mes', 'Mensal'),
            ('ano', 'Anual'),
        ],
        default='dia'
    )
    
    # Dados estatísticos (JSON)
    dados = models.JSONField('Dados Estatísticos', default=dict)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Estatística'
        verbose_name_plural = 'Estatísticas'
        unique_together = ['empresa', 'data_referencia', 'periodo_tipo']
        ordering = ['-data_referencia']
        indexes = [
            models.Index(fields=['empresa', 'periodo_tipo', '-data_referencia']),
        ]
    
    def __str__(self):
        return f'{self.empresa.razao_social} - {self.data_referencia} ({self.periodo_tipo})'
    
    @classmethod
    def calcular_estatisticas(cls, empresa, data_referencia, periodo_tipo='dia'):
        """Calcula estatísticas para empresa e período"""
        from coletas.models import Coleta, ColetaProfissional, StatusColeta, StatusPreenchimento
        
        # Define range de datas
        if periodo_tipo == 'dia':
            inicio = data_referencia
            fim = data_referencia + timedelta(days=1)
        elif periodo_tipo == 'semana':
            inicio = data_referencia - timedelta(days=data_referencia.weekday())
            fim = inicio + timedelta(days=7)
        elif periodo_tipo == 'mes':
            inicio = data_referencia.replace(day=1)
            if data_referencia.month == 12:
                fim = data_referencia.replace(year=data_referencia.year + 1, month=1, day=1)
            else:
                fim = data_referencia.replace(month=data_referencia.month + 1, day=1)
        else:  # ano
            inicio = data_referencia.replace(month=1, day=1)
            fim = data_referencia.replace(year=data_referencia.year + 1, month=1, day=1)
        
        # Coletas no período
        coletas_criadas = empresa.coletas.filter(
            created_at__gte=inicio,
            created_at__lt=fim
        ).count()
        
        coletas_concluidas = empresa.coletas.filter(
            status=StatusColeta.CONCLUIDA,
            data_fim__gte=inicio,
            data_fim__lt=fim
        ).count()
        
        # Profissionais que concluíram
        conclusoes = ColetaProfissional.objects.filter(
            coleta__empresa=empresa,
            status=StatusPreenchimento.CONCLUIDO,
            data_conclusao__gte=inicio,
            data_conclusao__lt=fim
        ).count()
        
        # Tempo médio de conclusão
        from django.db.models import Avg, F
        tempo_medio = ColetaProfissional.objects.filter(
            coleta__empresa=empresa,
            status=StatusPreenchimento.CONCLUIDO,
            data_conclusao__gte=inicio,
            data_conclusao__lt=fim
        ).aggregate(
            tempo_medio=Avg(F('data_conclusao') - F('data_inicio'))
        )['tempo_medio']
        
        if tempo_medio:
            tempo_medio_segundos = tempo_medio.total_seconds()
            tempo_medio_horas = round(tempo_medio_segundos / 3600, 2)
        else:
            tempo_medio_horas = 0
        
        # Novos profissionais
        novos_profissionais = empresa.profissionais.filter(
            created_at__gte=inicio,
            created_at__lt=fim
        ).count()
        
        dados = {
            'coletas_criadas': coletas_criadas,
            'coletas_concluidas': coletas_concluidas,
            'conclusoes_profissionais': conclusoes,
            'tempo_medio_horas': tempo_medio_horas,
            'novos_profissionais': novos_profissionais,
            'periodo': {
                'inicio': inicio.isoformat(),
                'fim': fim.isoformat(),
            }
        }
        
        # Criar ou atualizar
        estatistica, created = cls.objects.update_or_create(
            empresa=empresa,
            data_referencia=data_referencia,
            periodo_tipo=periodo_tipo,
            defaults={'dados': dados}
        )
        
        return estatistica


class Alerta(models.Model):
    """
    Alertas automáticos baseados em regras.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='alertas'
    )
    
    tipo = models.CharField(
        'Tipo',
        max_length=30,
        choices=[
            ('pendencia', 'Pendência de Coleta'),
            ('baixa_conclusao', 'Baixa Taxa de Conclusão'),
            ('prazo_vencido', 'Prazo Vencido'),
            ('inatividade', 'Inatividade de Profissionais'),
            ('erro_sistema', 'Erro do Sistema'),
        ]
    )
    severidade = models.CharField(
        'Severidade',
        max_length=20,
        choices=[
            ('info', 'Informação'),
            ('aviso', 'Aviso'),
            ('critico', 'Crítico'),
        ],
        default='info'
    )
    
    titulo = models.CharField('Título', max_length=255)
    mensagem = models.TextField('Mensagem')
    
    # Referências opcionais
    coleta = models.ForeignKey(
        'coletas.Coleta',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    profissional = models.ForeignKey(
        'empresas.Profissional',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alertas'
    )
    
    lido = models.BooleanField('Lido', default=False)
    resolvido = models.BooleanField('Resolvido', default=False)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa', 'lido', 'resolvido']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'{self.titulo} - {self.empresa.razao_social} ({self.severidade})'
    
    def marcar_lido(self):
        """Marca alerta como lido"""
        self.lido = True
        self.save()
    
    def marcar_resolvido(self):
        """Marca alerta como resolvido"""
        self.resolvido = True
        self.save()
    
    @classmethod
    def criar_alerta_pendencia(cls, coleta):
        """Cria alerta de pendência de coleta"""
        percentual = coleta.calcular_percentual()
        if percentual < 50:
            severidade = 'critico'
        elif percentual < 80:
            severidade = 'aviso'
        else:
            severidade = 'info'
        
        return cls.objects.create(
            empresa=coleta.empresa,
            tipo='pendencia',
            severidade=severidade,
            titulo=f'Pendência na coleta: {coleta.nome}',
            mensagem=f'A coleta {coleta.nome} está com {percentual}% de conclusão.',
            coleta=coleta
        )
    
    @classmethod
    def criar_alerta_prazo_vencido(cls, coleta):
        """Cria alerta de prazo vencido"""
        return cls.objects.create(
            empresa=coleta.empresa,
            tipo='prazo_vencido',
            severidade='critico',
            titulo=f'Prazo vencido: {coleta.nome}',
            mensagem=f'A coleta {coleta.nome} ultrapassou o prazo de conclusão.',
            coleta=coleta
        )

