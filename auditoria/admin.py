from django.contrib import admin
from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['data_hora', 'usuario_nome', 'tipo_acao', 'empresa', 'coleta', 'ip_address']
    list_filter = ['tipo_acao', 'data_hora', 'empresa']
    search_fields = ['usuario_nome', 'usuario_email', 'descricao']
    readonly_fields = ['id', 'data_hora', 'usuario', 'usuario_nome', 'usuario_email', 
                      'tipo_acao', 'descricao', 'empresa', 'coleta', 'dados_adicionais',
                      'ip_address', 'user_agent']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
