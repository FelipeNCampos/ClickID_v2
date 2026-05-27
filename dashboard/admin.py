"""
Admin configuration for dashboard app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Dashboard, Relatorio, Estatistica, Alerta


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin para modelo Dashboard"""
    list_display = ('empresa', 'periodo_padrao', 'auto_refresh', 'refresh_interval', 'total_widgets')
    list_filter = ('auto_refresh', 'periodo_padrao')
    search_fields = ('empresa__razao_social',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Empresa', {
            'fields': ('empresa',)
        }),
        ('Configurações', {
            'fields': ('widgets_ativos', 'layout', 'periodo_padrao')
        }),
        ('Auto-atualização', {
            'fields': ('auto_refresh', 'refresh_interval')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_widgets(self, obj):
        return len(obj.widgets_ativos) if isinstance(obj.widgets_ativos, list) else 0
    total_widgets.short_description = 'Total de Widgets'
    
    actions = ['resetar_layouts']
    
    def resetar_layouts(self, request, queryset):
        count = 0
        for dashboard in queryset:
            dashboard.resetar_layout()
            count += 1
        self.message_user(request, f'{count} dashboard(s) resetado(s) para configuração padrão.')
    resetar_layouts.short_description = 'Resetar layout para padrão'


@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    """Admin para modelo Relatorio"""
    list_display = ('tipo', 'empresa', 'gerado_por_nome', 'formato', 'status', 'tamanho_mb', 'created_at', 'expires_at')
    list_filter = ('tipo', 'formato', 'status', 'created_at', 'expires_at')
    search_fields = ('empresa__razao_social', 'gerado_por__email')
    readonly_fields = ('created_at', 'iniciado_em', 'concluido_em', 'tamanho', 'total_registros', 'erro')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'gerado_por', 'tipo', 'formato', 'status')
        }),
        ('Filtros Aplicados', {
            'fields': ('filtros',),
            'classes': ('collapse',)
        }),
        ('Arquivo', {
            'fields': ('arquivo', 'tamanho', 'total_registros')
        }),
        ('Processamento', {
            'fields': ('iniciado_em', 'concluido_em', 'erro'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    def gerado_por_nome(self, obj):
        return obj.gerado_por.email if obj.gerado_por else '-'
    gerado_por_nome.short_description = 'Gerado Por'
    
    def tamanho_mb(self, obj):
        if obj.tamanho > 0:
            return f'{obj.tamanho / (1024 * 1024):.2f} MB'
        return '-'
    tamanho_mb.short_description = 'Tamanho'
    
    actions = ['limpar_expirados', 'renovar_expiracao']
    
    def limpar_expirados(self, request, queryset):
        count = Relatorio.limpar_expirados()
        self.message_user(request, f'{count} relatório(s) expirado(s) removido(s).')
    limpar_expirados.short_description = 'Limpar relatórios expirados'
    
    def renovar_expiracao(self, request, queryset):
        count = 0
        for relatorio in queryset:
            relatorio.renovar_expiracao()
            count += 1
        self.message_user(request, f'{count} relatório(s) com expiração renovada por 30 dias.')
    renovar_expiracao.short_description = 'Renovar expiração (30 dias)'


@admin.register(Estatistica)
class EstatisticaAdmin(admin.ModelAdmin):
    """Admin para modelo Estatistica"""
    list_display = ('empresa', 'data_referencia', 'periodo_tipo', 'preview_dados', 'updated_at')
    list_filter = ('periodo_tipo', 'data_referencia', 'empresa')
    search_fields = ('empresa__razao_social',)
    readonly_fields = ('created_at', 'updated_at', 'dados')
    
    fieldsets = (
        ('Referência', {
            'fields': ('empresa', 'data_referencia', 'periodo_tipo')
        }),
        ('Dados Estatísticos', {
            'fields': ('dados',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_dados(self, obj):
        if isinstance(obj.dados, dict):
            items = []
            for key, value in list(obj.dados.items())[:3]:
                items.append(f'{key}: {value}')
            return ', '.join(items)
        return '-'
    preview_dados.short_description = 'Preview dos Dados'


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    """Admin para modelo Alerta"""
    list_display = ('titulo', 'empresa', 'tipo', 'severidade_badge', 'lido', 'resolvido', 'created_at')
    list_filter = ('tipo', 'severidade', 'lido', 'resolvido', 'created_at')
    search_fields = ('titulo', 'mensagem', 'empresa__razao_social')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informações', {
            'fields': ('empresa', 'tipo', 'severidade', 'titulo', 'mensagem')
        }),
        ('Relacionamentos', {
            'fields': ('coleta', 'profissional'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('lido', 'resolvido')
        }),
        ('Data', {
            'fields': ('created_at',)
        }),
    )
    
    def severidade_badge(self, obj):
        colors = {
            'info': '#17a2b8',
            'aviso': '#ffc107',
            'critico': '#dc3545',
        }
        color = colors.get(obj.severidade, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_severidade_display()
        )
    severidade_badge.short_description = 'Severidade'
    
    actions = ['marcar_como_lidos', 'marcar_como_resolvidos']
    
    def marcar_como_lidos(self, request, queryset):
        count = 0
        for alerta in queryset:
            alerta.marcar_lido()
            count += 1
        self.message_user(request, f'{count} alerta(s) marcado(s) como lido(s).')
    marcar_como_lidos.short_description = 'Marcar como lidos'
    
    def marcar_como_resolvidos(self, request, queryset):
        count = 0
        for alerta in queryset:
            alerta.marcar_resolvido()
            count += 1
        self.message_user(request, f'{count} alerta(s) marcado(s) como resolvido(s).')
    marcar_como_resolvidos.short_description = 'Marcar como resolvidos'

