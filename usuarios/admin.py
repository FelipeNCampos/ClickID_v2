"""
Admin configuration for usuarios app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario, Gerente, LogAuditoria


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    """Admin para modelo Usuario"""
    list_display = ('email', 'tipo_usuario', 'is_active', 'is_staff', 'created_at')
    list_filter = ('tipo_usuario', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Tipo'), {'fields': ('tipo_usuario',)}),
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Datas importantes'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'tipo_usuario', 'password1', 'password2'),
        }),
    )


@admin.register(Gerente)
class GerenteAdmin(admin.ModelAdmin):
    """Admin para modelo Gerente"""
    list_display = ('nome', 'cpf', 'telefone', 'usuario_email')
    list_filter = ()
    search_fields = ('nome', 'cpf', 'telefone', 'usuario__email')
    readonly_fields = ()
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('usuario', 'nome', 'cpf', 'telefone')
        }),

    )
    
    def usuario_email(self, obj):
        return obj.usuario.email
    usuario_email.short_description = 'Email'


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    """Admin para modelo LogAuditoria"""
    list_display = ('timestamp', 'usuario_email', 'acao', 'ip_address', 'user_agent')
    list_filter = ('acao', 'timestamp')
    search_fields = ('usuario__email', 'acao', 'descricao', 'ip_address')
    readonly_fields = ('timestamp', 'usuario', 'acao', 'descricao', 'ip_address', 'user_agent', 'dados_alterados')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('timestamp', 'usuario', 'acao')
        }),
        ('Detalhes', {
            'fields': ('descricao', 'dados_alterados')
        }),
        ('Contexto Técnico', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def usuario_email(self, obj):
        return obj.usuario.email if obj.usuario else '-'
    usuario_email.short_description = 'Usuário'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

