# ClickID v2.0 - GitHub Copilot Instructions

Sistema Django de coleta de dados multimídia com formulários dinâmicos, captura de fotos/assinaturas e arquitetura multi-tenant.

---

## 🏗️ Arquitetura Essencial

**Stack**: Django 5.2.8 + DRF 3.16.1 | JWT Auth | PostgreSQL/SQLite | S3 | Celery+Redis | openpyxl

**Apps Structure**:
```
usuarios/     → Custom User (gerente|empresa|profissional) + auth
empresas/     → Empresa, Profissional, Departamento (multi-tenant)
coletas/      → Coleta, ColetaProfissional, Respostas (lifecycle mgmt)
modelos/      → ModeloCartao, CampoCartao (canvas templates)
auditoria/    → LogAuditoria (system-wide audit trail)
dashboard/    → Metrics & KPIs
```

**URL Pattern**:
```
/api/v1/*                      → REST API (JWT required)
/gerente/*                     → Manager web UI
/empresa/*                     → Company web UI  
/profissional/*                → Professional web UI
/<empresa.url_personalizada>/  → Public company-specific URLs
```

**Dual Architecture** (CRITICAL):
- **REST API Layer**: DRF ViewSets with JWT authentication (`/api/v1/`)
- **Web Proxy Layer**: Django views that consume API with session-stored JWT
- **Why**: Separate concerns, reusable API, traditional web UX with Django templates

---

## ⚠️ Critical Patterns (Read This First)

### 1. Profissional PK Issue (🔴 FREQUENT BUG SOURCE)
```python
# ❌ WRONG - Profissional does NOT have 'id' field
profissionais = Profissional.objects.filter(id__in=ids)

# ✅ CORRECT - Uses 'usuario' OneToOneField as PK
profissionais = Profissional.objects.filter(usuario__in=ids)
```
**Why**: `Profissional.usuario` is a `OneToOneField(primary_key=True)`, not auto-generated `id`.  
**Location**: `empresas/models.py:91` - Always use `usuario` for Profissional queries.

### 2. Web View Proxy Pattern
```python
# empresas/web_views.py pattern
@empresa_required  # Custom decorator checks tipo_usuario
def view_name(request, pk=None):
    """Proxy to API endpoint using session JWT"""
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    
    response = requests.get(
        f'http://127.0.0.1:8000/api/v1/resource/{pk}/',
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        return render(request, 'template.html', {'data': data})
    else:
        messages.error(request, 'Error message')
        return redirect('web-empresa:dashboard')
```
**Why**: Web views don't duplicate business logic, just proxy authenticated API calls.  
**Token Storage**: JWT stored in `request.session['access_token']` after login.

### 3. Mandatory Audit Logging
```python
# After EVERY critical action in ViewSets
from auditoria.models import LogAuditoria, TipoAcao

LogAuditoria.registrar(
    usuario=request.user,
    tipo_acao=TipoAcao.COLETA_INICIADA,
    descricao=f"Coleta '{coleta.nome}' iniciada com {total} profissionais",
    empresa=empresa,              # Optional FK context
    coleta=coleta,                # Optional FK context
    dados_adicionais={'count': total},  # Optional JSON metadata
    request=request               # Auto-captures IP + user agent
)
```
**When**: coleta_criada, coleta_iniciada, coleta_cancelada, participante_adicionado, participante_removido, exportacao.  
**Location**: `auditoria/models.py:97-127` - classmethod handles IP/user agent extraction.

### 4. UUID Primary Keys Everywhere
```python
# All new models MUST use UUIDs
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
```
**Why**: Multi-tenant security, prevents ID enumeration, distributed system friendly.  
**Exception**: Profissional (uses usuario FK as PK).

---

## 🔄 State Machines

### Coleta Status Flow
```
RASCUNHO → EM_ANDAMENTO → CONCLUIDA
              ↓
           CANCELADA (terminal state)
```
**Key Rule**: Only `em_andamento` accepts responses. Location: `coletas/models.py:11-17`

### ColetaProfissional Status
```
PENDENTE → EM_PROGRESSO → CONCLUIDO
              ↓
          EXPIRADO (if prazo exceeded)
```

---

## 🛠️ Critical Development Workflows

### Running the Server
```powershell
python manage.py runserver
# API: http://127.0.0.1:8000/api/v1/
# Web: http://127.0.0.1:8000/empresa/
```

### Database Migrations
```powershell
python manage.py makemigrations <app_name>
python manage.py migrate
# Check for pending: python manage.py showmigrations
```

### Testing
```powershell
python manage.py test                    # All tests
python manage.py test <app_name>         # App-specific
python manage.py test <app>.<TestClass>  # Specific test class
```

### Debugging Common Issues
```powershell
# Check logs directory
Get-Content logs\app.log -Tail 50

# Shell debugging
python manage.py shell
>>> from empresas.models import Profissional
>>> Profissional.objects.filter(usuario__in=[uuid1, uuid2])  # NOT id__in!

# Migration conflicts
python manage.py migrate --fake <app_name> <migration_number>
```

---

## 📝 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Models | PascalCase | `ColetaProfissional` |
| Functions/Methods | snake_case | `adicionar_profissionais()` |
| ViewSet Actions | snake_case | `@action def exportar_excel()` |
| URL Names | kebab-case | `name='coletas-list'` |
| Template Files | snake_case | `coleta_detail.html` |
| Constants/Enums | UPPER_SNAKE | `StatusColeta.EM_ANDAMENTO` |

---

## 🔐 Authentication Details

**JWT Tokens**: `djangorestframework-simplejwt` with custom user model.

**Login Credentials**:
- **Gerente/Empresa**: Email + password
- **Profissional**: CPF (no formatting) + password (default: last 4 CPF digits)

**Token Storage**:
- API clients: Send `Authorization: Bearer <token>` header
- Web views: Store in `request.session['access_token']`

**User Types** (usuarios/models.py:44-49):
```python
tipo_usuario in ['gerente', 'empresa', 'profissional']
```

---

## 📦 Export Patterns

### Excel (openpyxl)
```python
import openpyxl
from datetime import datetime

wb = openpyxl.Workbook()
ws = wb.active

# ALWAYS include generation timestamp
ws['A1'] = 'Gerado em:'
ws['B1'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

# ... data population ...

response = HttpResponse(
    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
response['Content-Disposition'] = f'attachment; filename="{filename}"'
wb.save(response)
return response
```

### CSV (UTF-8 BOM for Excel)
```python
import csv

response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
response['Content-Disposition'] = 'attachment; filename="data.csv"'
response.write('\ufeff')  # UTF-8 BOM for Excel compatibility
writer = csv.writer(response)
```

### ZIP (In-Memory with folder structure)
```python
import zipfile
from io import BytesIO

zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    # Structure: {CPF}/foto.jpg, {CPF}/assinatura.png
    zip_file.writestr(f"{cpf_sem_pontos}/foto.jpg", foto_data)
```

---

## 🎨 Frontend Stack

**Bootstrap 5.3** + **Bootstrap Icons** (`<i class="bi bi-icon-name"></i>`)

**Template Structure**:
```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Page Title - ClickID{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="{% url 'web-empresa:dashboard' %}">Dashboard</a></li>
            <li class="breadcrumb-item active">Current Page</li>
        </ol>
    </nav>
    <!-- Content -->
</div>
{% endblock %}
```

**Date Formatting** (JavaScript):
```javascript
new Date(isoString).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
}); // Output: "15/11/2025 14:30"
```

---

## 🚨 Common Pitfalls

1. **Using `id__in` on Profissional** → Use `usuario__in` (see section 1 above)
2. **Forgetting audit logs** → Add `LogAuditoria.registrar()` after state changes
3. **Hardcoding localhost URLs** → Use `reverse()` or relative paths
4. **Missing CSRF token** → Always `{% csrf_token %}` in forms
5. **Missing timestamp in exports** → Required for audit compliance
6. **Not handling 404 in proxy views** → Always check `response.status_code`

---

## 📚 Additional Resources

**Full Documentation**:
- `prompts/nomenclatura.md` - Complete naming guide
- `prompts/arquitetura.md` - Detailed pattern library  
- `prompts/templates.md` - Prompt templates for common tasks
- `docs/HU/` - User stories (requirements)
- `docs/UML/` - Architecture diagrams

**Key Files to Reference**:
- `clickid_core/settings.py` - Configuration patterns
- `empresas/web_views.py` - Proxy pattern examples
- `coletas/views.py` - Audit logging examples
- `auditoria/models.py` - TipoAcao enum and registrar() method
- `usuarios/models.py` - Custom User implementation

---

**Last Updated**: November 2025 | **Django**: 5.2.8 | **DRF**: 3.16.1
class MinhaSerializer(serializers.ModelSerializer):
    # Campos adicionais computados
    campo_extra = serializers.SerializerMethodField()
    
    class Meta:
        model = MinhaModel
        fields = ['id', 'nome', 'descricao', 'campo_extra']
        read_only_fields = ['id', 'criado_em']
    
    def get_campo_extra(self, obj):
        return obj.calcular_algo()
```

### Frontend/Templates

#### HTML/Django Templates
- Use Bootstrap 5.3 para componentes UI
- Bootstrap Icons para ícones
- Estrutura de template: `{% extends 'base.html' %}`
- Sempre use `{% csrf_token %}` em forms

#### Estrutura Padrão de Template
```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Título da Página - ClickID{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Breadcrumb -->
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="{% url 'web-empresa:dashboard' %}">Dashboard</a></li>
            <li class="breadcrumb-item active">Página Atual</li>
        </ol>
    </nav>
    
    <!-- Conteúdo -->
</div>
{% endblock %}

{% block extra_js %}
<script>
    // JavaScript adicional aqui
</script>
{% endblock %}
```

#### JavaScript
- Use vanilla JavaScript sempre que possível
- Bootstrap 5 JS para componentes interativos
- Formato de datas: `dd/mm/yyyy HH:MM`
- Use `toLocaleString('pt-BR')` para formatação

### URLs

#### Padrão de Nomeação
- API REST: `/api/v1/<recurso>/`
- Views Web Empresa: `/empresa/<acao>/`
- Views Web Gerente: `/gerente/<acao>/`
- Views Profissional: `/<url-personalizada>/` (slug da empresa)

#### Convenção de nomes de URL
```python
# API
path('api/v1/coletas/', include('coletas.urls'))

# Web
path('empresa/coletas/', views.coletas_list, name='coletas-list')
path('empresa/coletas/<uuid:pk>/', views.coleta_detail, name='coleta-detail')
```

## Padrões de Implementação

### Auditoria
Sempre registrar ações críticas:
```python
from auditoria.models import LogAuditoria, TipoAcao

LogAuditoria.registrar(
    usuario=request.user,
    tipo_acao=TipoAcao.COLETA_INICIADA,
    descricao=f"Coleta '{coleta.nome}' iniciada",
    empresa=empresa,
    coleta=coleta,
    dados_adicionais={'campo': 'valor'},
    request=request  # Para capturar IP e user agent
)
```

### Exportação de Dados
#### Excel
```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from django.http import HttpResponse
from datetime import datetime

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Nome da Planilha"

# Sempre incluir timestamp de geração
ws['A1'] = 'Gerado em:'
ws['B1'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

# Preparar resposta
response = HttpResponse(
    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
filename = f"arquivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
response['Content-Disposition'] = f'attachment; filename="{filename}"'
wb.save(response)
return response
```

#### CSV
```python
import csv
from django.http import HttpResponse

response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
response['Content-Disposition'] = f'attachment; filename="dados.csv"'

# BOM para compatibilidade com Excel
response.write('\ufeff')

writer = csv.writer(response)
writer.writerow(['Coluna1', 'Coluna2'])
```

### Proxy Views (Web para API)
```python
@empresa_required
def minha_view(request, pk):
    """Proxy web view para endpoint API"""
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    
    try:
        response = requests.get(
            f'http://127.0.0.1:8000/api/v1/recurso/{pk}/',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return render(request, 'template.html', {'data': data})
        else:
            messages.error(request, 'Erro ao buscar dados')
            return redirect('web-empresa:dashboard')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return redirect('web-empresa:dashboard')
```

## Regras de Negócio Importantes

### Coletas
1. **Estados de Coleta**:
   - `rascunho`: Criada mas não iniciada
   - `em_andamento`: Profissionais podem responder
   - `concluida`: Finalizada, não aceita mais respostas
   - `cancelada`: Interrompida, não pode ser reaberta

2. **ColetaProfissional Status**:
   - `pendente`: Não iniciou
   - `em_progresso`: Iniciou mas não finalizou
   - `concluido`: Finalizou o formulário
   - `expirado`: Prazo vencido

3. **Adição de Profissionais**:
   - Se "todos profissionais" marcado, adiciona automaticamente todos ativos da empresa
   - Senão, adiciona individualmente por IDs
   - IMPORTANTE: Profissional usa `usuario` como PK, não `id`. Use `usuario__in` em queries

### Autenticação
- JWT com access/refresh tokens
- Session storage no frontend web
- Profissionais fazem login com CPF (sem pontuação)
- Gerentes/Empresas fazem login com email

### Mídias
- Armazenamento: AWS S3 (produção) ou local (dev)
- Tipos: fotos (.jpg, .png), assinaturas (.png)
- Organização em ZIP: `{CPF_sem_pontos}/foto.jpg` e `{CPF_sem_pontos}/assinatura.png`

## Troubleshooting Comum

### Erro: "Cannot resolve keyword 'id'"
- Profissional usa `usuario` como PK, não `id`
- Use `Profissional.objects.filter(usuario__in=ids)` ao invés de `id__in`

### Erro: "Pillow is not installed"
- ImageField requer Pillow: `pip install Pillow`

### Erro de Migração
```bash
python manage.py makemigrations <app_name>
python manage.py migrate <app_name>
```

## Testes

### Executar Testes
```bash
python manage.py test
python manage.py test <app_name>
python manage.py test <app_name>.tests.<TestClass>
```

### Estrutura de Teste
```python
from django.test import TestCase
from django.contrib.auth import get_user_model

class MinhaTestCase(TestCase):
    def setUp(self):
        """Configuração antes de cada teste"""
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
    
    def test_algo(self):
        """Nome descritivo do que está sendo testado"""
        resultado = funcao_testada()
        self.assertEqual(resultado, esperado)
```

## Comandos Úteis

### Django
```bash
# Servidor de desenvolvimento
python manage.py runserver

# Migrações
python manage.py makemigrations
python manage.py migrate

# Shell interativo
python manage.py shell

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

### Celery
```bash
# Worker
celery -A clickid_core worker -l info

# Beat (tarefas agendadas)
celery -A clickid_core beat -l info
```

## Recursos Adicionais

### Documentação Oficial
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Bootstrap: https://getbootstrap.com/docs/5.3/
- openpyxl: https://openpyxl.readthedocs.io/

### Estrutura de Diretórios
```
ClickID_v2/
├── auditoria/          # Sistema de logs
├── clickid_core/       # Settings e configs
├── coletas/            # App principal de coletas
├── dashboard/          # Dashboards
├── empresas/           # Gestão de empresas
├── modelos/            # Templates de cartões
├── usuarios/           # Autenticação
├── templates/          # Templates Django
│   ├── base.html
│   ├── empresas/
│   ├── gerente/
│   └── profissional/
├── static/             # Assets estáticos
├── media/              # Uploads de usuários
├── logs/               # Arquivos de log
├── docs/               # Documentação
└── requirements.txt    # Dependências Python
```

## Notas de Versão

### v2.0 - Novembro 2025
- ✅ Sistema completo de auditoria
- ✅ Exportações avançadas (Excel, CSV, ZIP)
- ✅ Remoção de participantes com log
- ✅ Página de visualização de logs
- ✅ Correção de bugs no modelo Profissional
- ✅ Melhorias de UI/UX em dashboards
