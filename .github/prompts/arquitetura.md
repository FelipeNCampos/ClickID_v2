# Padrões de Arquitetura - ClickID v2.0

## Arquitetura Geral

### Camadas da Aplicação
```
┌─────────────────────────────────────────┐
│         Frontend (Templates)            │
│    Bootstrap 5.3 + Vanilla JS          │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│        Web Views (Proxy Layer)          │
│   Empresas/Web Views, Auth Session     │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│          REST API (DRF)                 │
│   ViewSets, Serializers, JWT Auth      │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│         Business Logic                  │
│      Models, Managers, Services         │
└─────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│           Data Layer                    │
│    PostgreSQL/SQLite + AWS S3           │
└─────────────────────────────────────────┘
```

## Estrutura de Apps Django

### 1. Core App (clickid_core)
**Responsabilidade**: Configurações centrais e roteamento principal

**Arquivos principais**:
- `settings.py`: Configurações Django
- `urls.py`: URL routing raiz
- `wsgi.py`/`asgi.py`: Server entry points

### 2. Apps de Domínio

#### A. **usuarios/**
**Responsabilidade**: Autenticação e gestão de usuários

**Models**:
- `Usuario`: User customizado (email login)
- `Gerente`: Perfil de gerente
- `Profissional`: Perfil de profissional (PK = usuario!)

**Views**:
- API: `UsuarioViewSet`, `GerenteViewSet`, `ProfissionalViewSet`
- Web: Login, logout, registro

#### B. **empresas/**
**Responsabilidade**: Gestão de empresas clientes

**Models**:
- `Empresa`: Dados da empresa (url_personalizada única)
- `Departamento`: Departamentos da empresa

**Views**:
- API: `EmpresaViewSet`, `DepartamentoViewSet`
- Web: Dashboard empresa, gestão de profissionais
- Public: Página pública de login (via url_personalizada)

#### C. **modelos/**
**Responsabilidade**: Templates de cartões e formulários

**Models**:
- `ModeloCartao`: Template de cartão com canvas
- `CampoFormulario`: Campos dinâmicos do formulário

**Views**:
- API: CRUD de modelos
- Web: Editor de canvas, preview

#### D. **coletas/**
**Responsabilidade**: Núcleo do sistema de coletas

**Models**:
- `Coleta`: Coleta de dados
- `ColetaProfissional`: M2M entre Coleta e Profissional
- `Resposta`: Respostas do formulário
- `Foto`, `Assinatura`: Mídias coletadas

**Views**:
- API: `ColetaViewSet` com actions customizadas
  - `adicionar_profissionais`
  - `iniciar`, `cancelar`, `finalizar`, `reabrir`
  - `exportar_excel`, `exportar_dados_textuais`
  - `exportar_participantes_csv`, `exportar_midias`
  - `remover_participante`
- Web: Dashboard, detalhes, gerenciamento

#### E. **auditoria/**
**Responsabilidade**: Logging e rastreamento de ações

**Models**:
- `LogAuditoria`: Registro de todas as ações críticas

**Views**:
- API: `LogAuditoriaViewSet` (read-only)
- Web: Página de visualização de logs

#### F. **dashboard/**
**Responsabilidade**: Métricas e estatísticas

**Views**:
- API: Agregações e KPIs
- Web: Dashboards visuais

## Padrões de Views

### 1. API ViewSets (DRF)

**Estrutura básica**:
```python
class ColetaViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de coletas"""
    queryset = Coleta.objects.filter(is_active=True)
    serializer_class = ColetaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por empresa do usuário"""
        return super().get_queryset().filter(empresa=self.request.user.empresa)
    
    @action(detail=True, methods=['post'])
    def minha_acao(self, request, pk=None):
        """Action customizada"""
        objeto = self.get_object()
        # Lógica aqui
        return Response({'status': 'success'})
```

**Actions customizadas**:
- Use `@action(detail=True, methods=['post'])` para ações em instância específica
- Use `@action(detail=False, methods=['get'])` para ações em lista
- Sempre incluir docstring
- Sempre registrar auditoria para ações críticas

### 2. Web Views (Proxy Layer)

**Padrão de proxy para API**:
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

**Padrão de export file**:
```python
@empresa_required
def coleta_exportar_excel(request, pk):
    """Exportar dados da coleta para Excel"""
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    
    response = requests.get(
        f'http://127.0.0.1:8000/api/v1/coletas/{pk}/exportar_excel/',
        headers=headers,
        stream=True
    )
    
    if response.status_code == 200:
        http_response = HttpResponse(
            response.content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
            http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return http_response
    
    messages.error(request, 'Erro ao exportar dados')
    return redirect('web-empresa:coleta-detail', pk=pk)
```

## Padrões de Models

### 1. Model Base
```python
class MinhaModel(models.Model):
    """Docstring clara"""
    
    # PK UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Keys
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE)
    
    # Campos obrigatórios
    nome = models.CharField('Nome', max_length=200)
    
    # Campos opcionais
    descricao = models.TextField('Descrição', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Minha Model'
        verbose_name_plural = 'Minhas Models'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['-criado_em']),
            models.Index(fields=['empresa', 'is_active']),
        ]
    
    def __str__(self):
        return self.nome
```

### 2. Managers Customizados
```python
class ColetaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    
    def em_andamento(self):
        return self.filter(status='em_andamento')
    
    def por_empresa(self, empresa):
        return self.filter(empresa=empresa)

class Coleta(models.Model):
    # ... campos ...
    
    objects = ColetaManager()
    all_objects = models.Manager()  # Para acessar deletados
```

### 3. Properties e Métodos
```python
class Coleta(models.Model):
    # ... campos ...
    
    @property
    def total_profissionais(self):
        """Número total de profissionais na coleta"""
        return self.coleta_profissionais.count()
    
    def calcular_percentual(self):
        """Calcula percentual de conclusão"""
        if self.total_profissionais == 0:
            return 0
        return int((self.total_concluidos / self.total_profissionais) * 100)
    
    def iniciar(self):
        """Inicia a coleta"""
        if self.status != 'rascunho':
            raise ValueError('Apenas coletas em rascunho podem ser iniciadas')
        self.status = 'em_andamento'
        self.data_inicio = timezone.now()
        self.save()
```

## Padrões de Serializers

### 1. Serializer Básico
```python
class ColetaSerializer(serializers.ModelSerializer):
    # Campos computados
    total_profissionais = serializers.SerializerMethodField()
    percentual_conclusao = serializers.SerializerMethodField()
    
    # Campos relacionados
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    modelo_nome = serializers.CharField(source='modelo.nome', read_only=True)
    
    class Meta:
        model = Coleta
        fields = [
            'id', 'nome', 'descricao', 'status',
            'empresa', 'empresa_nome', 'modelo', 'modelo_nome',
            'total_profissionais', 'percentual_conclusao',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def get_total_profissionais(self, obj):
        return obj.total_profissionais
    
    def get_percentual_conclusao(self, obj):
        return obj.calcular_percentual()
```

### 2. Nested Serializers
```python
class ProfissionalSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = ['usuario', 'nome', 'cpf', 'email']

class ColetaProfissionalSerializer(serializers.ModelSerializer):
    profissional = ProfissionalSimpleSerializer(read_only=True)
    
    class Meta:
        model = ColetaProfissional
        fields = ['id', 'profissional', 'status', 'data_conclusao']
```

## Padrões de Templates

### 1. Estrutura Base
```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Título - ClickID{% endblock %}

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
    // JavaScript específico da página
</script>
{% endblock %}
```

### 2. Cards Bootstrap
```django
<div class="card">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0"><i class="bi bi-icon"></i> Título</h5>
    </div>
    <div class="card-body">
        <!-- Conteúdo -->
    </div>
    <div class="card-footer bg-transparent">
        <a href="#" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-arrow-right"></i> Ver mais
        </a>
    </div>
</div>
```

### 3. Tabelas Responsivas
```django
<div class="table-responsive">
    <table class="table table-hover">
        <thead>
            <tr>
                <th>Coluna 1</th>
                <th>Coluna 2</th>
                <th class="text-end">Ações</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.campo1 }}</td>
                <td>{{ item.campo2 }}</td>
                <td class="text-end">
                    <a href="#" class="btn btn-sm btn-info">
                        <i class="bi bi-eye"></i>
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

## Padrões de Auditoria

### 1. Registro de Auditoria
```python
from auditoria.models import LogAuditoria, TipoAcao

# Em uma action do ViewSet
LogAuditoria.registrar(
    usuario=request.user,
    tipo_acao=TipoAcao.COLETA_INICIADA,
    descricao=f"Coleta '{coleta.nome}' iniciada",
    empresa=coleta.empresa,
    coleta=coleta,
    dados_adicionais={
        'total_profissionais': coleta.total_profissionais,
        'modelo': coleta.modelo.nome if coleta.modelo else None
    },
    request=request  # Para capturar IP e user agent
)
```

### 2. Tipos de Ação
- `COLETA_CRIADA`: Quando uma nova coleta é criada
- `COLETA_INICIADA`: Quando uma coleta sai de rascunho
- `COLETA_CANCELADA`: Quando uma coleta é cancelada
- `COLETA_CONCLUIDA`: Quando uma coleta é finalizada forçosamente
- `COLETA_REABERTA`: Quando uma coleta é reaberta
- `PARTICIPANTE_ADICIONADO`: Quando profissionais são adicionados
- `PARTICIPANTE_REMOVIDO`: Quando um profissional é removido

## Padrões de Exportação

### 1. Excel (openpyxl)
```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from django.http import HttpResponse
from datetime import datetime

def exportar_excel(self, request, pk=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dados"
    
    # Sempre incluir timestamp
    ws['A1'] = 'Gerado em:'
    ws['B1'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # Estilização
    header_fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Dados...
    
    # Resposta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"arquivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
```

### 2. CSV
```python
import csv
from django.http import HttpResponse

def exportar_csv(self, request, pk=None):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f"dados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # BOM para Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    writer.writerow(['Coluna1', 'Coluna2'])
    
    for item in dados:
        writer.writerow([item.campo1, item.campo2])
    
    return response
```

### 3. ZIP (arquivos múltiplos)
```python
import zipfile
import io
from django.http import HttpResponse

def exportar_midias(self, request, pk=None):
    memoria = io.BytesIO()
    
    with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in itens:
            if os.path.exists(item.arquivo.path):
                zf.write(
                    item.arquivo.path,
                    arcname=f"{item.pasta}/{os.path.basename(item.arquivo.path)}"
                )
    
    memoria.seek(0)
    
    response = HttpResponse(memoria, content_type='application/zip')
    filename = f"midias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
```

## Padrões de Segurança

### 1. Decorators de Autorização
```python
from functools import wraps
from django.shortcuts import redirect

def empresa_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('access_token'):
            return redirect('web-gerente:login')
        if request.user.tipo != 'empresa':
            return redirect('web-gerente:login')
        return view_func(request, *args, **kwargs)
    return wrapper
```

### 2. Permissions DRF
```python
from rest_framework import permissions

class IsEmpresaOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.empresa == request.user.empresa
```

## Padrões de Testes

### 1. Test Case Básico
```python
from django.test import TestCase
from django.contrib.auth import get_user_model

class ColetaTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass123',
            tipo='empresa'
        )
        self.empresa = Empresa.objects.create(
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
    
    def test_criar_coleta(self):
        coleta = Coleta.objects.create(
            nome='Teste',
            empresa=self.empresa,
            status='rascunho'
        )
        self.assertEqual(coleta.nome, 'Teste')
        self.assertEqual(coleta.status, 'rascunho')
```

### 2. API Test
```python
from rest_framework.test import APITestCase
from rest_framework import status

class ColetaAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_listar_coletas(self):
        response = self.client.get('/api/v1/coletas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```
