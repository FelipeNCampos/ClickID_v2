"""
Admin configuration for coletas app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Coleta, ColetaProfissional, RespostaColeta, RespostaCampo,
    Foto, Assinatura, Notificacao, LogEmail
)


class ColetaProfissionalInline(admin.TabularInline):
    """Inline para profissionais da coleta"""
    model = ColetaProfissional
    extra = 0
    readonly_fields = ('status', 'data_inicio', 'data_conclusao')
    fields = ('profissional', 'status', 'data_inicio', 'data_conclusao')


@admin.register(Coleta)
class ColetaAdmin(admin.ModelAdmin):
    """Admin para modelo Coleta"""
    list_display = ('nome', 'empresa', 'status', 'percentual_conclusao', 'total_profissionais', 'total_concluidos', 'created_at')
    list_filter = ('status', 'empresa', 'created_at')
    search_fields = ('nome', 'empresa__razao_social')
    readonly_fields = ('created_at', 'updated_at', 'total_profissionais', 'total_concluidos', 'percentual_conclusao')
    inlines = [ColetaProfissionalInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'modelo', 'iniciado_por', 'nome', 'status')
        }),
        ('Configurações', {
            'fields': ('include_foto', 'include_assinatura', 'include_dados')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim', 'prazo')
        }),
        ('Estatísticas', {
            'fields': ('total_profissionais', 'total_concluidos', 'percentual_conclusao'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['finalizar_coletas', 'cancelar_coletas', 'reabrir_coletas']
    
    def percentual_conclusao(self, obj):
        percentual = obj.calcular_percentual()
        if percentual >= 80:
            color = 'green'
        elif percentual >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{percentual:.1f}%'
        )
    percentual_conclusao.short_description = 'Conclusão'
    
    def finalizar_coletas(self, request, queryset):
        count = 0
        for coleta in queryset:
            coleta.finalizar()
            count += 1
        self.message_user(request, f'{count} coleta(s) finalizada(s).')
    finalizar_coletas.short_description = 'Finalizar coletas selecionadas'
    
    def cancelar_coletas(self, request, queryset):
        count = 0
        for coleta in queryset:
            coleta.cancelar()
            count += 1
        self.message_user(request, f'{count} coleta(s) cancelada(s).')
    cancelar_coletas.short_description = 'Cancelar coletas selecionadas'
    
    def reabrir_coletas(self, request, queryset):
        count = 0
        for coleta in queryset:
            coleta.reabrir()
            count += 1
        self.message_user(request, f'{count} coleta(s) reaberta(s).')
    reabrir_coletas.short_description = 'Reabrir coletas selecionadas'


@admin.register(ColetaProfissional)
class ColetaProfissionalAdmin(admin.ModelAdmin):
    """Admin para modelo ColetaProfissional"""
    list_display = ('coleta', 'profissional', 'status', 'data_inicio', 'data_conclusao')
    list_filter = ('status', 'coleta__empresa', 'data_inicio', 'data_conclusao')
    search_fields = ('coleta__nome', 'profissional__nome', 'profissional__cpf')
    readonly_fields = ('data_inicio', 'data_conclusao', 'ip_address')
    
    fieldsets = (
        ('Relacionamento', {
            'fields': ('coleta', 'profissional')
        }),
        ('Status', {
            'fields': ('status', 'data_inicio', 'data_conclusao')
        }),
        ('Contexto Técnico', {
            'fields': ('ip_address',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['finalizar_preenchimentos']
    
    def finalizar_preenchimentos(self, request, queryset):
        count = 0
        for cp in queryset:
            cp.finalizar()
            count += 1
        self.message_user(request, f'{count} preenchimento(s) finalizado(s).')
    finalizar_preenchimentos.short_description = 'Finalizar preenchimentos selecionados'


class RespostaCampoInline(admin.TabularInline):
    """Inline para respostas de campos"""
    model = RespostaCampo
    extra = 0
    readonly_fields = ('campo', 'valor_texto', 'valor_numero', 'valor_data', 'valor_json')
    fields = ('campo', 'valor_texto', 'valor_numero', 'valor_data')


@admin.register(RespostaColeta)
class RespostaColetaAdmin(admin.ModelAdmin):
    """Admin para modelo RespostaColeta"""
    list_display = ('profissional_nome', 'coleta_nome', 'created_at', 'updated_at')
    list_filter = ('created_at', 'coleta_profissional__coleta__empresa')
    search_fields = ('coleta_profissional__profissional__nome', 'coleta_profissional__coleta__nome')
    readonly_fields = ('coleta_profissional', 'created_at', 'updated_at')
    inlines = [RespostaCampoInline]
    
    def profissional_nome(self, obj):
        return obj.coleta_profissional.profissional.nome
    profissional_nome.short_description = 'Profissional'
    
    def coleta_nome(self, obj):
        return obj.coleta_profissional.coleta.nome
    coleta_nome.short_description = 'Coleta'


@admin.register(RespostaCampo)
class RespostaCampoAdmin(admin.ModelAdmin):
    """Admin para modelo RespostaCampo"""
    list_display = ('campo_nome', 'resposta_profissional', 'obter_valor')
    list_filter = ('campo__tipo',)
    search_fields = ('campo__nome_campo', 'resposta_coleta__coleta_profissional__profissional__nome')
    readonly_fields = ('resposta_coleta', 'campo', 'valor_texto', 'valor_numero', 'valor_data', 'valor_json')
    
    def campo_nome(self, obj):
        return obj.campo.nome_campo
    campo_nome.short_description = 'Campo'
    
    def resposta_profissional(self, obj):
        return obj.resposta_coleta.coleta_profissional.profissional.nome
    resposta_profissional.short_description = 'Profissional'


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    """Admin para modelo Foto"""
    list_display = ('profissional_nome', 'tamanho_mb', 'formato', 'resolucao', 'uploaded_at')
    list_filter = ('formato', 'uploaded_at')
    search_fields = ('resposta_coleta__coleta_profissional__profissional__nome',)
    readonly_fields = ('resposta_coleta', 'tamanho', 'formato', 'resolucao', 'uploaded_at', 'preview_image')
    
    fieldsets = (
        ('Informações', {
            'fields': ('resposta_coleta', 'arquivo', 'preview_image')
        }),
        ('Detalhes Técnicos', {
            'fields': ('tamanho', 'formato', 'resolucao', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profissional_nome(self, obj):
        return obj.resposta_coleta.coleta_profissional.profissional.nome
    profissional_nome.short_description = 'Profissional'
    
    def tamanho_mb(self, obj):
        return f'{obj.tamanho / (1024 * 1024):.2f} MB'
    tamanho_mb.short_description = 'Tamanho'
    
    def preview_image(self, obj):
        if obj.arquivo:
            return format_html('<img src="{}" width="200" />', obj.arquivo.url)
        return '-'
    preview_image.short_description = 'Preview'


@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    """Admin para modelo Assinatura"""
    list_display = ('profissional_nome', 'tamanho_kb', 'formato', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('resposta_coleta__coleta_profissional__profissional__nome',)
    readonly_fields = ('resposta_coleta', 'tamanho', 'formato', 'uploaded_at', 'preview_image')
    
    fieldsets = (
        ('Informações', {
            'fields': ('resposta_coleta', 'arquivo', 'preview_image')
        }),
        ('Detalhes Técnicos', {
            'fields': ('tamanho', 'formato', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profissional_nome(self, obj):
        return obj.resposta_coleta.coleta_profissional.profissional.nome
    profissional_nome.short_description = 'Profissional'
    
    def tamanho_kb(self, obj):
        return f'{obj.tamanho / 1024:.2f} KB'
    tamanho_kb.short_description = 'Tamanho'
    
    def preview_image(self, obj):
        if obj.arquivo:
            return format_html('<img src="{}" width="200" />', obj.arquivo.url)
        return '-'
    preview_image.short_description = 'Preview'


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    """Admin para modelo Notificacao"""
    list_display = ('tipo', 'destinatario', 'assunto', 'enviado_em', 'lido', 'tentativas_envio')
    list_filter = ('tipo', 'lido', 'enviado_em', 'created_at')
    search_fields = ('destinatario__email', 'assunto', 'mensagem')
    readonly_fields = ('created_at', 'enviado_em', 'tentativas_envio')
    
    fieldsets = (
        ('Informações', {
            'fields': ('destinatario', 'tipo', 'assunto', 'mensagem')
        }),
        ('Relacionamento', {
            'fields': ('coleta_profissional',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('enviado_em', 'lido', 'tentativas_envio')
        }),
        ('Datas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_como_lidas', 'reenviar_notificacoes']
    
    def marcar_como_lidas(self, request, queryset):
        count = queryset.update(lido=True)
        self.message_user(request, f'{count} notificação(ões) marcada(s) como lida(s).')
    marcar_como_lidas.short_description = 'Marcar como lidas'
    
    def reenviar_notificacoes(self, request, queryset):
        count = 0
        for notificacao in queryset:
            if notificacao.reenviar():
                count += 1
        self.message_user(request, f'{count} notificação(ões) reenviada(s).')
    reenviar_notificacoes.short_description = 'Reenviar notificações'


@admin.register(LogEmail)
class LogEmailAdmin(admin.ModelAdmin):
    """Admin para modelo LogEmail"""
    list_display = ('destinatario', 'assunto', 'status', 'enviado_em')
    list_filter = ('status', 'enviado_em')
    search_fields = ('destinatario', 'assunto', 'erro')
    readonly_fields = ('notificacao', 'destinatario', 'assunto', 'enviado_em', 'status', 'erro')
    
    fieldsets = (
        ('Informações', {
            'fields': ('notificacao', 'destinatario', 'assunto', 'status')
        }),
        ('Erro', {
            'fields': ('erro',),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('enviado_em',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

