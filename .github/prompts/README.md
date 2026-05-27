# README - Prompts e Convenções

Este diretório contém documentação de referência rápida para padronização do desenvolvimento do projeto ClickID v2.0.

## Arquivos

### 📝 nomenclatura.md
**Propósito**: Convenções de nomenclatura para todos os elementos do código

**Use quando**:
- Criar novos models, views, functions
- Nomear variáveis, constantes, classes
- Criar arquivos, URLs, templates
- Definir IDs HTML ou classes CSS
- Escrever mensagens e labels

**Conteúdo**:
- Padrões Python/Django (PascalCase, snake_case, UPPER_SNAKE_CASE)
- Padrões Templates (IDs, classes, arquivos)
- Padrões URLs (paths, names, namespaces)
- Padrões JavaScript (camelCase)
- Regras especiais (Profissional model, UUIDs)
- Exemplos completos

### 🏗️ arquitetura.md
**Propósito**: Padrões arquiteturais e estruturais do projeto

**Use quando**:
- Criar novos apps ou módulos
- Implementar ViewSets e Serializers
- Criar templates e views
- Adicionar auditoria
- Implementar exportações
- Configurar segurança e testes

**Conteúdo**:
- Arquitetura em camadas
- Estrutura de apps Django
- Padrões de Views (API e Web)
- Padrões de Models (base, managers, properties)
- Padrões de Serializers
- Padrões de Templates Bootstrap
- Padrões de Auditoria
- Padrões de Exportação (Excel, CSV, ZIP)
- Padrões de Segurança
- Padrões de Testes

### 📋 templates.md
**Propósito**: Templates de prompts prontos para uso com GitHub Copilot

**Use quando**:
- Solicitar criação de código novo
- Pedir refatoração de código existente
- Corrigir bugs
- Adicionar features

**Conteúdo**:
- 10 templates de prompts:
  1. Criar Novo Model
  2. Criar ViewSet com Actions
  3. Criar Template Django
  4. Criar Proxy View
  5. Adicionar Auditoria
  6. Criar Exportação
  7. Criar Migrations
  8. Adicionar Validação
  9. Refatorar Código
  10. Corrigir Bug

## Como Usar

### Para Desenvolvimento Normal

1. **Antes de escrever código**, consulte `nomenclatura.md` para garantir que está usando os nomes corretos
2. **Ao criar novos componentes**, consulte `arquitetura.md` para seguir os padrões estabelecidos
3. **Ao solicitar código ao Copilot**, use os templates de `templates.md` preenchendo os placeholders

### Fluxo de Trabalho Recomendado

```
┌─────────────────────────────────────┐
│   1. Entender a Tarefa              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   2. Consultar nomenclatura.md      │
│      para nomes corretos            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   3. Consultar arquitetura.md       │
│      para padrões relevantes        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   4. Usar template.md               │
│      para gerar prompt              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   5. Implementar com Copilot        │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   6. Revisar contra padrões         │
└─────────────────────────────────────┘
```

### Exemplos de Uso

#### Exemplo 1: Criar um novo Model

1. Abra `templates.md` → Seção "1. Criar Novo Model"
2. Copie o template
3. Preencha com suas informações:
```
Crie um novo model Django chamado Alerta no app usuarios com os seguintes campos:
- titulo: CharField max 200 (obrigatório)
- mensagem: TextField (obrigatório)
- lido: BooleanField default False (obrigatório)
- profissional: ForeignKey para Profissional (obrigatório)

Requisitos:
- Use UUID como chave primária
- Inclua timestamps (criado_em, atualizado_em)
- Adicione campo is_active para soft delete
- Siga as convenções de nomenclatura do projeto
- Inclua docstring explicativa
- Adicione Meta class com verbose_name e ordering
```
4. Cole no Copilot Chat

#### Exemplo 2: Implementar uma Action no ViewSet

1. Abra `templates.md` → Seção "2. Criar ViewSet com Actions"
2. Adapte para sua action específica
3. Consulte `arquitetura.md` → Seção "Padrões de Views" para referência
4. Consulte `nomenclatura.md` para nomes corretos
5. Monte o prompt completo e envie ao Copilot

#### Exemplo 3: Criar Template de Lista

1. Abra `templates.md` → Seção "3. Criar Template Django"
2. Preencha os detalhes da sua lista
3. Consulte `arquitetura.md` → Seção "Padrões de Templates" para estrutura
4. Envie ao Copilot

## Referência Rápida

### Nomenclatura Mais Comum

| Elemento | Formato | Exemplo |
|----------|---------|---------|
| Model | PascalCase | `ColetaProfissional` |
| Função | snake_case | `adicionar_profissionais()` |
| Constante | UPPER_SNAKE_CASE | `STATUS_CHOICES` |
| Variável | snake_case | `coleta_profissionais` |
| Template | snake_case.html | `coleta_detail.html` |
| URL name | kebab-case | `'coleta-detail'` |
| URL path | kebab-case | `'coletas/<pk>/'` |
| ID HTML | camelCase | `#loginLink` |
| JS função | camelCase | `filtrarProfissionais()` |

### Imports Comuns

```python
# Models
from django.db import models
import uuid
from django.utils import timezone

# Views API
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# Views Web
from django.shortcuts import render, redirect
from django.contrib import messages
import requests

# Auditoria
from auditoria.models import LogAuditoria, TipoAcao

# Exportação
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from django.http import HttpResponse
from datetime import datetime
```

### Estrutura Padrão de Action

```python
@action(detail=True, methods=['post'])
def minha_acao(self, request, pk=None):
    """Descrição clara da ação"""
    objeto = self.get_object()
    
    try:
        # 1. Validações
        # 2. Lógica principal
        # 3. Auditoria (se crítico)
        
        LogAuditoria.registrar(
            usuario=request.user,
            tipo_acao=TipoAcao.ACAO_REALIZADA,
            descricao=f"...",
            empresa=objeto.empresa,
            coleta=objeto,
            request=request
        )
        
        return Response({'status': 'success'})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
```

## Manutenção

### Atualizando esta Documentação

Quando adicionar novos padrões ou convenções:

1. **nomenclatura.md**: Adicione na seção apropriada com exemplos
2. **arquitetura.md**: Adicione padrão completo com código de exemplo
3. **templates.md**: Crie novo template de prompt
4. **README.md** (este arquivo): Atualize índice e referências

### Sugestões de Melhoria

Se encontrar casos não cobertos ou ambiguidades:

1. Documente o caso na issue do GitHub
2. Proponha adição/modificação nos arquivos
3. Inclua exemplos práticos
4. Solicite review do time

## Documentação Adicional

Para informações mais detalhadas sobre o projeto:
- `.github/copilot-instructions.md`: Instruções completas do projeto para o GitHub Copilot
- `docs/`: Diagramas UML e documentação técnica
- `API_ENDPOINTS.md`: Documentação dos endpoints da API
- `README.md` (raiz): Visão geral do projeto

---

**Última atualização**: 19/11/2025  
**Versão**: 2.0
