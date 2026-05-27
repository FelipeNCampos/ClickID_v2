"""
Admin configuration for modelos app
"""
from django.contrib import admin
from .models import ModeloCartao, CampoCartao


class CampoCartaoInline(admin.TabularInline):
    """Inline para campos do modelo de cartão"""
    model = CampoCartao
    extra = 1
    fields = ('nome_campo', 'tipo', 'obrigatorio', 'ordem', 'posicao_x', 'posicao_y', 'largura', 'altura')
    ordering = ('ordem',)


@admin.register(ModeloCartao)
class ModeloCartaoAdmin(admin.ModelAdmin):
    """Admin para modelo ModeloCartao"""
    list_display = ('nome', 'empresa', 'largura_mm', 'altura_mm', 'dpi', 'total_campos', 'is_active', 'created_at')
    list_filter = ('is_active', 'empresa', 'created_at')
    search_fields = ('nome', 'descricao', 'empresa__razao_social')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CampoCartaoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'descricao')
        }),
        ('Dimensões do Cartão', {
            'fields': ('largura_mm', 'altura_mm', 'dpi')
        }),
        ('Aparência', {
            'fields': ('background_image', 'background_color')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_campos(self, obj):
        return obj.campos.count()
    total_campos.short_description = 'Total de Campos'


@admin.register(CampoCartao)
class CampoCartaoAdmin(admin.ModelAdmin):
    """Admin para modelo CampoCartao"""
    list_display = ('nome_campo', 'modelo', 'tipo', 'obrigatorio', 'ordem', 'posicao_x', 'posicao_y')
    list_filter = ('tipo', 'obrigatorio', 'modelo__empresa')
    search_fields = ('nome_campo', 'pergunta_formulario', 'modelo__nome')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('modelo', 'nome_campo', 'tipo', 'obrigatorio', 'ordem')
        }),
        ('Configuração do Formulário', {
            'fields': ('pergunta_formulario', 'placeholder', 'texto_ajuda', 'opcoes', 'validacao_regex'),
            'classes': ('collapse',)
        }),
        ('Posicionamento no Cartão (mm)', {
            'fields': ('posicao_x', 'posicao_y', 'largura', 'altura')
        }),
        ('Estilo Visual', {
            'fields': (
                'fonte', 'tamanho_fonte', 'cor_texto',
                'alinhamento', 'negrito', 'italico', 'sublinhado', 'rotacao'
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('modelo', 'ordem')

