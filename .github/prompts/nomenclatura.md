# Convenções de Nomenclatura - ClickID v2.0

## Python/Django

### 1. Classes
- **Formato**: PascalCase
- **Exemplos**:
  - `ModeloCartao`
  - `ColetaProfissional`
  - `LogAuditoria`
  - `DashboardEmpresa`

### 2. Funções e Métodos
- **Formato**: snake_case
- **Exemplos**:
  - `adicionar_profissionais()`
  - `exportar_excel()`
  - `calcular_percentual()`
  - `registrar_auditoria()`

### 3. Constantes
- **Formato**: UPPER_SNAKE_CASE
- **Exemplos**:
  - `TIPO_ACAO_CHOICES`
  - `STATUS_CHOICES`
  - `MAX_FILE_SIZE`
  - `DEFAULT_TIMEOUT`

### 4. Variáveis
- **Formato**: snake_case
- **Exemplos**:
  - `coleta_profissionais`
  - `data_inicio`
  - `total_concluidos`
  - `profissionais_ids`

### 5. Atributos de Model
- **Formato**: snake_case
- **Ordem**:
  1. Chave primária (UUID)
  2. Foreign Keys
  3. Campos obrigatórios
  4. Campos opcionais
  5. Timestamps (criado_em, atualizado_em)

**Exemplo**:
```python
class Coleta(models.Model):
    # PK
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Keys
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE)
    modelo = models.ForeignKey('modelos.ModeloCartao', on_delete=models.SET_NULL, null=True)
    
    # Campos obrigatórios
    nome = models.CharField('Nome', max_length=200)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES)
    
    # Campos opcionais
    descricao = models.TextField('Descrição', blank=True, null=True)
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
```

## Templates Django

### 1. Arquivos de Template
- **Formato**: snake_case.html
- **Exemplos**:
  - `dashboard_empresa.html`
  - `coleta_detail.html`
  - `profissionais_list.html`
  - `login.html`

### 2. IDs HTML
- **Formato**: camelCase
- **Exemplos**:
  - `#loginLink`
  - `#filtroStatus`
  - `#tabelaProfissionais`
  - `#modalRemoverParticipante`

### 3. Classes CSS Personalizadas
- **Formato**: kebab-case
- **Usar Bootstrap primeiro, depois customizar**
- **Exemplos**:
  - `.data-formatada`
  - `.profissional-row`
  - `.card-coleta`

## URLs

### 1. Nomes de URL (name)
- **Formato**: kebab-case
- **Padrão**: `<entidade>-<acao>`
- **Exemplos**:
  - `name='coletas-list'`
  - `name='coleta-detail'`
  - `name='coleta-exportar-dados-textuais'`
  - `name='dashboard-empresa'`

### 2. Paths de URL
- **Formato**: kebab-case
- **Exemplos**:
  - `/empresa/coletas/`
  - `/empresa/coletas/<uuid:pk>/`
  - `/empresa/coletas/<uuid:pk>/exportar-dados-textuais/`
  - `/gerente/dashboard/`

### 3. Namespaces
- **Formato**: kebab-case com hífen
- **Exemplos**:
  - `namespace='web-empresa'`
  - `namespace='web-gerente'`
  - `namespace='api-v1'`

## JavaScript

### 1. Variáveis e Funções
- **Formato**: camelCase
- **Exemplos**:
  - `filtrarProfissionais()`
  - `copyLoginLink()`
  - `confirmarRemocao()`
  - `const loginLink = ...`

### 2. Constantes
- **Formato**: UPPER_SNAKE_CASE (se for global/config)
- **Exemplos**:
  - `const MAX_RETRIES = 3`
  - `const API_BASE_URL = '...'`

## Arquivos e Diretórios

### 1. Apps Django
- **Formato**: snake_case (plural quando apropriado)
- **Exemplos**:
  - `coletas/`
  - `empresas/`
  - `usuarios/`
  - `auditoria/`

### 2. Módulos Python
- **Formato**: snake_case
- **Exemplos**:
  - `views.py`
  - `web_views.py`
  - `serializers.py`
  - `web_urls.py`

### 3. Arquivos Estáticos
- **Formato**: kebab-case
- **Exemplos**:
  - `style-custom.css`
  - `dashboard-charts.js`
  - `logo-empresa.png`

## Mensagens e Textos

### 1. Mensagens de Sucesso
- **Formato**: Descritivo, positivo, português
- **Exemplos**:
  - `"Coleta iniciada com sucesso!"`
  - `"Participante removido com sucesso!"`
  - `"Dados exportados com sucesso!"`

### 2. Mensagens de Erro
- **Formato**: Descritivo, informativo, português
- **Exemplos**:
  - `"Erro ao iniciar coleta. Tente novamente."`
  - `"Nenhuma resposta concluída encontrada."`
  - `f"Erro: {str(e)}"`

### 3. Labels e Títulos
- **Formato**: Title Case em português
- **Exemplos**:
  - `"Nome da Coleta"`
  - `"Data de Início"`
  - `"Total de Profissionais"`

## Documentação

### 1. Docstrings Python
- **Formato**: Triple quotes, descrição concisa
- **Exemplos**:
```python
def adicionar_profissionais(self, request, pk=None):
    """Adicionar profissionais a uma coleta"""
    ...

class ColetaViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de coletas"""
    ...
```

### 2. Comentários
- **Formato**: # para linha única, descrição clara
- **Exemplos**:
```python
# Registrar no log de auditoria
LogAuditoria.registrar(...)

# Cabeçalho da tabela de profissionais
headers = ['Profissional', 'CPF', 'Status']
```

## Regras Especiais

### 1. Profissional Model
- **PK**: Usa `usuario` (OneToOneField), NÃO `id`
- **Queries**: Sempre use `usuario__in` ao invés de `id__in`
- **Exemplo**:
```python
# ❌ ERRADO
Profissional.objects.filter(id__in=profissionais_ids)

# ✅ CORRETO
Profissional.objects.filter(usuario__in=profissionais_ids)
```

### 2. UUIDs
- Sempre use UUIDField como PK em novos models
- Formato: `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`

### 3. Timestamps
- Sempre incluir em models:
  - `criado_em = models.DateTimeField(auto_now_add=True)`
  - `atualizado_em = models.DateTimeField(auto_now=True)`

### 4. Soft Delete
- Usar campo `is_active = models.BooleanField(default=True)`
- Não deletar fisicamente registros importantes

## Exemplos Completos

### Model Completo
```python
class Coleta(models.Model):
    """Modelo para gerenciar coletas de dados"""
    
    # PK
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Keys
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE)
    modelo = models.ForeignKey('modelos.ModeloCartao', on_delete=models.SET_NULL, null=True)
    
    # Campos obrigatórios
    nome = models.CharField('Nome', max_length=200)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES)
    
    # Campos opcionais
    descricao = models.TextField('Descrição', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Coleta'
        verbose_name_plural = 'Coletas'
        ordering = ['-criado_em']
    
    def __str__(self):
        return self.nome
```

### ViewSet Action Completo
```python
@action(detail=True, methods=['post'])
def adicionar_profissionais(self, request, pk=None):
    """Adicionar profissionais a uma coleta"""
    coleta = self.get_object()
    profissionais_ids = request.data.get('profissionais_ids', [])
    todos_profissionais = request.data.get('todos_profissionais', False)
    
    try:
        # Lógica aqui
        
        # Registrar auditoria
        LogAuditoria.registrar(
            usuario=request.user,
            tipo_acao=TipoAcao.PARTICIPANTE_ADICIONADO,
            descricao=f"Profissionais adicionados à coleta '{coleta.nome}'",
            empresa=coleta.empresa,
            coleta=coleta,
            request=request
        )
        
        return Response({'status': 'success'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

### Template Completo
```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Título - ClickID{% endblock %}

{% block content %}
<div class="container-fluid py-4">
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            <li class="breadcrumb-item"><a href="{% url 'web-empresa:dashboard' %}">Dashboard</a></li>
            <li class="breadcrumb-item active">Página</li>
        </ol>
    </nav>
    
    <!-- Conteúdo -->
</div>
{% endblock %}

{% block extra_js %}
<script>
    function minhaFuncao() {
        // JavaScript aqui
    }
</script>
{% endblock %}
```
