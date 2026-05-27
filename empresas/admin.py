"""
Admin configuration for empresas app
"""
from django.contrib import admin
from .models import Empresa, Departamento, Profissional


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """Admin para modelo Empresa"""
    list_display = ('razao_social', 'cnpj', 'url_personalizada', 'usuario_email', 'data_cadastro')
    list_filter = ('data_cadastro',)
    search_fields = ('razao_social', 'cnpj', 'url_personalizada', 'usuario__email')
    readonly_fields = ('data_cadastro',)
    
    fieldsets = (
        ('Dados da Empresa', {
            'fields': ('usuario', 'razao_social', 'nome_fantasia', 'cnpj', 'url_personalizada', 'logo')
        }),
        ('Contato', {
            'fields': ('telefone', 'endereco')
        }),
        ('Cadastro', {
            'fields': ('cadastrado_por', 'data_cadastro'),
            'classes': ('collapse',)
        }),
    )
    
    def usuario_email(self, obj):
        return obj.usuario.email
    usuario_email.short_description = 'Email de Login'


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    """Admin para modelo Departamento"""
    list_display = ('nome', 'empresa', 'total_profissionais', 'created_at')
    list_filter = ('empresa', 'created_at')
    search_fields = ('nome', 'descricao', 'empresa__razao_social')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'descricao')
        }),
        ('Datas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def total_profissionais(self, obj):
        return obj.profissionais.count()
    total_profissionais.short_description = 'Total de Profissionais'


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    """Admin para modelo Profissional"""
    list_display = ('nome', 'cpf', 'empresa', 'departamento', 'senha_alterada', 'data_cadastro')
    list_filter = ('senha_alterada', 'empresa', 'departamento', 'data_cadastro')
    search_fields = ('nome', 'cpf', 'email', 'empresa__razao_social')
    readonly_fields = ('data_primeiro_login', 'data_cadastro')
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('usuario', 'empresa', 'departamento', 'nome', 'cpf', 'email')
        }),
        ('Cadastro', {
            'fields': ('cadastrado_por', 'data_cadastro'),
            'classes': ('collapse',)
        }),
        ('Acesso', {
            'fields': ('senha_alterada', 'data_primeiro_login')
        }),
    )
    
    actions = ['resetar_senha_padrao']
    
    def resetar_senha_padrao(self, request, queryset):
        """Ação para resetar senha para padrão (últimos 4 dígitos do CPF)"""
        count = 0
        for profissional in queryset:
            profissional.senha_alterada = False
            profissional.save()
            count += 1
        self.message_user(request, f'{count} senha(s) resetada(s) para o padrão.')
    resetar_senha_padrao.short_description = 'Resetar senha para padrão (4 últimos dígitos CPF)'

