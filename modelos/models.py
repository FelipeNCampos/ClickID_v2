"""
Models do app modelos - Sistema ClickID
Gerenciamento de modelos de cartões canvas e campos personalizáveis
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class TipoCampo(models.TextChoices):
    """Tipos de campos disponíveis para formulários"""
    TEXTO_CURTO = 'texto_curto', 'Texto Curto'
    TEXTO_LONGO = 'texto_longo', 'Texto Longo'
    EMAIL = 'email', 'E-mail'
    CPF = 'cpf', 'CPF'
    TELEFONE = 'telefone', 'Telefone'
    DATA = 'data', 'Data'
    NUMERO = 'numero', 'Número'
    FOTO = 'foto', 'Foto'
    ASSINATURA = 'assinatura', 'Assinatura'
    SELECAO_UNICA = 'selecao_unica', 'Seleção Única'
    SELECAO_MULTIPLA = 'selecao_multipla', 'Seleção Múltipla'
    CODIGO_BARRAS = 'codigo_barras', 'Código de Barras'
    QR_CODE = 'qr_code', 'QR Code'
    IMAGEM_ESTATICA = 'imagem_estatica', 'Imagem Estática'


class ModeloCartao(models.Model):
    """
    Modelo de cartão PRIVADO por empresa.
    Design em canvas drag-and-drop com dimensões reais.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='modelos'
    )
    nome = models.CharField('Nome do Modelo', max_length=255)
    descricao = models.TextField('Descrição', blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Dimensões do cartão
    largura_mm = models.FloatField(
        'Largura (mm)',
        default=85.6,
        validators=[MinValueValidator(10), MaxValueValidator(500)]
    )
    altura_mm = models.FloatField(
        'Altura (mm)',
        default=54.0,
        validators=[MinValueValidator(10), MaxValueValidator(500)]
    )
    dpi = models.IntegerField(
        'DPI',
        default=300,
        validators=[MinValueValidator(72), MaxValueValidator(600)]
    )
    
    # Design
    background_image = models.ImageField(
        'Imagem de Fundo (Frente)',
        upload_to='modelos/backgrounds/',
        null=True,
        blank=True
    )
    background_color = models.CharField(
        'Cor de Fundo (Frente)',
        max_length=7,
        default='#FFFFFF',
        help_text='Formato: #RRGGBB'
    )
    background_image_verso = models.ImageField(
        'Imagem de Fundo (Verso)',
        upload_to='modelos/backgrounds/',
        null=True,
        blank=True
    )
    background_color_verso = models.CharField(
        'Cor de Fundo (Verso)',
        max_length=7,
        default='#FFFFFF',
        help_text='Formato: #RRGGBB'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Modelo de Cartão'
        verbose_name_plural = 'Modelos de Cartões'
        ordering = ['-created_at']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return f'{self.empresa.razao_social} - {self.nome}'
    
    def validar_dimensoes(self):
        """Valida se as dimensões estão dentro dos limites"""
        return (10 <= self.largura_mm <= 500 and 
                10 <= self.altura_mm <= 500)
    
    def exportar_preview(self):
        """Gera preview do cartão (implementar com canvas renderer)"""
        # TODO: Implementar geração de preview
        pass
    
    @property
    def total_campos(self):
        return self.campos.count()


class CampoCartao(models.Model):
    """
    Campo do cartão com configurações visuais e de formulário.
    Dual configuration: aparência no cartão + pergunta do formulário.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modelo = models.ForeignKey(
        ModeloCartao,
        on_delete=models.CASCADE,
        related_name='campos'
    )
    
    # Configurações Básicas
    nome_campo = models.CharField('Nome do Campo', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TipoCampo.choices)
    obrigatorio = models.BooleanField('Obrigatório', default=True)
    ordem = models.IntegerField('Ordem', default=0)
    lado = models.CharField(
        'Lado do Cartão',
        max_length=10,
        choices=[('frente', 'Frente'), ('verso', 'Verso')],
        default='frente'
    )
    
    # Configurações do Formulário
    pergunta_formulario = models.CharField(
        'Pergunta no Formulário',
        max_length=500,
        help_text='Texto que aparecerá como pergunta para o profissional'
    )
    placeholder = models.CharField(
        'Placeholder',
        max_length=255,
        blank=True,
        help_text='Texto de exemplo no campo'
    )
    texto_ajuda = models.CharField(
        'Texto de Ajuda',
        max_length=500,
        blank=True,
        help_text='Instrução adicional para preenchimento'
    )
    opcoes = models.JSONField(
        'Opções',
        null=True,
        blank=True,
        help_text='Para seleção única/múltipla: lista de opções'
    )
    validacao_regex = models.CharField(
        'Regex de Validação',
        max_length=500,
        blank=True
    )
    
    # Configurações Visuais no Cartão (Canvas)
    posicao_x = models.FloatField(
        'Posição X (mm)',
        default=0,
        validators=[MinValueValidator(0)]
    )
    posicao_y = models.FloatField(
        'Posição Y (mm)',
        default=0,
        validators=[MinValueValidator(0)]
    )
    largura = models.FloatField(
        'Largura (mm)',
        default=50,
        validators=[MinValueValidator(1)]
    )
    altura = models.FloatField(
        'Altura (mm)',
        default=10,
        validators=[MinValueValidator(1)]
    )
    
    # Estilização de Texto
    fonte = models.CharField(
        'Fonte',
        max_length=100,
        default='Arial',
        help_text='Nome da fonte (Arial, Times New Roman, etc.)'
    )
    tamanho_fonte = models.IntegerField(
        'Tamanho da Fonte',
        default=12,
        validators=[MinValueValidator(6), MaxValueValidator(72)]
    )
    cor_texto = models.CharField(
        'Cor do Texto',
        max_length=7,
        default='#000000',
        help_text='Formato: #RRGGBB'
    )
    alinhamento = models.CharField(
        'Alinhamento',
        max_length=10,
        choices=[
            ('left', 'Esquerda'),
            ('center', 'Centro'),
            ('right', 'Direita'),
            ('justify', 'Justificado'),
        ],
        default='left'
    )
    negrito = models.BooleanField('Negrito', default=False)
    italico = models.BooleanField('Itálico', default=False)
    sublinhado = models.BooleanField('Sublinhado', default=False)
    rotacao = models.FloatField(
        'Rotação (graus)',
        default=0,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    
    class Meta:
        verbose_name = 'Campo do Cartão'
        verbose_name_plural = 'Campos do Cartão'
        ordering = ['modelo', 'ordem']
        unique_together = ['modelo', 'nome_campo']
    
    def __str__(self):
        return f'{self.modelo.nome} - {self.nome_campo} ({self.get_tipo_display()})'
    
    def validar(self):
        """Valida configurações do campo"""
        # Validar se posições estão dentro das dimensões do cartão
        if self.posicao_x + self.largura > self.modelo.largura_mm:
            return False, 'Campo ultrapassa largura do cartão'
        if self.posicao_y + self.altura > self.modelo.altura_mm:
            return False, 'Campo ultrapassa altura do cartão'
        return True, 'OK'
    
    def aplicar_estilo(self):
        """Retorna dicionário com estilos CSS para preview"""
        return {
            'font-family': self.fonte,
            'font-size': f'{self.tamanho_fonte}pt',
            'color': self.cor_texto,
            'text-align': self.alinhamento,
            'font-weight': 'bold' if self.negrito else 'normal',
            'font-style': 'italic' if self.italico else 'normal',
            'text-decoration': 'underline' if self.sublinhado else 'none',
            'transform': f'rotate({self.rotacao}deg)',
        }
    
    def calcular_posicao_absoluta(self):
        """Calcula posição em pixels baseado no DPI"""
        dpi = self.modelo.dpi
        mm_to_inch = 0.0393701
        x_px = self.posicao_x * mm_to_inch * dpi
        y_px = self.posicao_y * mm_to_inch * dpi
        return {'x': x_px, 'y': y_px}

    def save(self, *args, **kwargs):
        """Validações adicionais para garantir exclusividade por modelo"""
        if CampoCartao.objects.filter(modelo=self.modelo, nome_campo=self.nome_campo).exclude(id=self.id).exists():
            raise ValueError(f"Já existe um campo com o nome '{self.nome_campo}' neste modelo.")
        super().save(*args, **kwargs)
