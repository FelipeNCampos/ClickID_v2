# API Endpoints - ClickID v2

## Visão Geral
API RESTful completa com autenticação JWT para gerenciamento de coletas de dados multimedia.

**Base URL**: `http://localhost:8000/api/v1/`

## Autenticação

### Login
```http
POST /api/v1/usuarios/login/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "senha123"
}

Response 200:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { ... }
}
```

### Refresh Token
```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Usuários

### Listar Usuários
```http
GET /api/v1/usuarios/
Authorization: Bearer {access_token}
```

### Usuário Atual
```http
GET /api/v1/usuarios/me/
Authorization: Bearer {access_token}
```

### Alterar Senha
```http
POST /api/v1/usuarios/change_password/
Authorization: Bearer {access_token}

{
  "old_password": "senha_antiga",
  "new_password": "senha_nova",
  "confirm_password": "senha_nova"
}
```

## Gerentes

```http
GET    /api/v1/gerentes/           # Listar gerentes
POST   /api/v1/gerentes/           # Criar gerente
GET    /api/v1/gerentes/{id}/      # Detalhes do gerente
PUT    /api/v1/gerentes/{id}/      # Atualizar gerente
DELETE /api/v1/gerentes/{id}/      # Deletar gerente
POST   /api/v1/gerentes/{id}/toggle_active/  # Ativar/desativar
```

## Empresas

```http
GET    /api/v1/empresas/                      # Listar empresas
POST   /api/v1/empresas/                      # Criar empresa
GET    /api/v1/empresas/{id}/                 # Detalhes
PUT    /api/v1/empresas/{id}/                 # Atualizar
DELETE /api/v1/empresas/{id}/                 # Deletar
GET    /api/v1/empresas/{id}/profissionais/   # Profissionais da empresa
GET    /api/v1/empresas/{id}/departamentos/   # Departamentos
GET    /api/v1/empresas/{id}/estatisticas/    # Estatísticas
```

## Departamentos

```http
GET    /api/v1/departamentos/                # Listar departamentos
POST   /api/v1/departamentos/                # Criar departamento
GET    /api/v1/departamentos/{id}/           # Detalhes
PUT    /api/v1/departamentos/{id}/           # Atualizar
DELETE /api/v1/departamentos/{id}/           # Deletar
GET    /api/v1/departamentos/{id}/profissionais/  # Profissionais do depto

Filtros:
?empresa_id={uuid}
```

## Profissionais

```http
GET    /api/v1/profissionais/                # Listar profissionais
POST   /api/v1/profissionais/                # Criar profissional
GET    /api/v1/profissionais/{id}/           # Detalhes
PUT    /api/v1/profissionais/{id}/           # Atualizar
DELETE /api/v1/profissionais/{id}/           # Deletar
POST   /api/v1/profissionais/import_excel/   # Importar via Excel
POST   /api/v1/profissionais/bulk_create/    # Criar múltiplos
POST   /api/v1/profissionais/{id}/resetar_senha/  # Resetar senha
GET    /api/v1/profissionais/{id}/coletas/   # Coletas do profissional

Filtros:
?empresa_id={uuid}
?departamento_id={uuid}
?is_active=true
```

## Modelos de Cartão

```http
GET    /api/v1/modelos-cartao/               # Listar modelos
POST   /api/v1/modelos-cartao/               # Criar modelo
GET    /api/v1/modelos-cartao/{id}/          # Detalhes
PUT    /api/v1/modelos-cartao/{id}/          # Atualizar
DELETE /api/v1/modelos-cartao/{id}/          # Deletar
POST   /api/v1/modelos-cartao/{id}/duplicate/  # Duplicar modelo
GET    /api/v1/modelos-cartao/{id}/preview/  # Preview do modelo

Filtros:
?empresa_id={uuid}
?is_active=true
```

## Campos do Cartão

```http
GET    /api/v1/campos-cartao/                # Listar campos
POST   /api/v1/campos-cartao/                # Criar campo
GET    /api/v1/campos-cartao/{id}/           # Detalhes
PUT    /api/v1/campos-cartao/{id}/           # Atualizar
DELETE /api/v1/campos-cartao/{id}/           # Deletar
POST   /api/v1/campos-cartao/reorder/        # Reordenar campos
GET    /api/v1/campos-cartao/tipos_disponiveis/  # Tipos de campo

Filtros:
?modelo_id={uuid}
?tipo=texto_curto
```

## Coletas

```http
GET    /api/v1/coletas/                      # Listar coletas
POST   /api/v1/coletas/                      # Criar coleta
GET    /api/v1/coletas/{id}/                 # Detalhes
PUT    /api/v1/coletas/{id}/                 # Atualizar
DELETE /api/v1/coletas/{id}/                 # Deletar
POST   /api/v1/coletas/{id}/iniciar/         # Iniciar coleta
POST   /api/v1/coletas/{id}/cancelar/        # Cancelar coleta
POST   /api/v1/coletas/{id}/finalizar/       # Finalizar coleta
POST   /api/v1/coletas/{id}/reabrir/         # Reabrir coleta
GET    /api/v1/coletas/{id}/estatisticas/    # Estatísticas

Filtros:
?empresa_id={uuid}
?status=em_andamento
?modelo_id={uuid}
```

### Iniciar Coleta
```http
POST /api/v1/coletas/{id}/iniciar/

{
  "profissionais_ids": ["uuid1", "uuid2"],
  "departamentos_ids": ["uuid3"],
  "todos_profissionais": false,
  "enviar_notificacao": true
}
```

## Coletas dos Profissionais

```http
GET    /api/v1/coletas-profissionais/        # Listar
POST   /api/v1/coletas-profissionais/        # Criar
GET    /api/v1/coletas-profissionais/{id}/   # Detalhes
PUT    /api/v1/coletas-profissionais/{id}/   # Atualizar
POST   /api/v1/coletas-profissionais/{id}/iniciar_preenchimento/
POST   /api/v1/coletas-profissionais/{id}/finalizar_preenchimento/

Filtros:
?coleta_id={uuid}
?profissional_id={uuid}
?status=pendente
```

## Respostas de Coleta

```http
GET    /api/v1/respostas-coletas/            # Listar
POST   /api/v1/respostas-coletas/            # Criar resposta completa
GET    /api/v1/respostas-coletas/{id}/       # Detalhes

Filtros:
?coleta_profissional_id={uuid}
```

### Criar Resposta Completa
```http
POST /api/v1/respostas-coletas/
Content-Type: multipart/form-data

{
  "coleta_profissional_id": "uuid",
  "respostas": [
    {"campo_id": "uuid1", "valor": "texto"},
    {"campo_id": "uuid2", "valor": 123}
  ],
  "foto": (binary),
  "assinatura": (binary)
}
```

## Notificações

```http
GET    /api/v1/notificacoes/                 # Listar notificações
POST   /api/v1/notificacoes/                 # Criar notificação
GET    /api/v1/notificacoes/{id}/            # Detalhes
POST   /api/v1/notificacoes/{id}/marcar_lida/  # Marcar como lida
POST   /api/v1/notificacoes/marcar_todas_lidas/  # Marcar todas

Filtros:
?lido=false
?tipo=coleta_iniciada
```

## Dashboard

```http
GET    /api/v1/dashboard/                    # Listar dashboards
POST   /api/v1/dashboard/                    # Criar dashboard
GET    /api/v1/dashboard/{id}/               # Detalhes
PUT    /api/v1/dashboard/{id}/               # Atualizar
GET    /api/v1/dashboard/{id}/estatisticas/  # Estatísticas gerais
POST   /api/v1/dashboard/{id}/configurar/    # Configurar dashboard
POST   /api/v1/dashboard/{id}/adicionar_widget/  # Adicionar widget
POST   /api/v1/dashboard/{id}/remover_widget/   # Remover widget
POST   /api/v1/dashboard/{id}/resetar/       # Resetar para padrão
```

## Relatórios

```http
GET    /api/v1/relatorios/                   # Listar relatórios
POST   /api/v1/relatorios/                   # Criar relatório
GET    /api/v1/relatorios/{id}/              # Detalhes
DELETE /api/v1/relatorios/{id}/              # Deletar
POST   /api/v1/relatorios/{id}/baixar/       # Baixar arquivo
POST   /api/v1/relatorios/{id}/renovar/      # Renovar expiração
POST   /api/v1/relatorios/limpar_expirados/  # Limpar expirados

Filtros:
?tipo=coletas_geral
?status=concluido
```

### Criar Relatório
```http
POST /api/v1/relatorios/

{
  "tipo": "coletas_detalhado",
  "formato": "pdf",
  "data_inicio": "2025-01-01",
  "data_fim": "2025-12-31",
  "coleta_id": "uuid" (opcional)
}
```

## Alertas

```http
GET    /api/v1/alertas/                      # Listar alertas
POST   /api/v1/alertas/                      # Criar alerta
GET    /api/v1/alertas/{id}/                 # Detalhes
PUT    /api/v1/alertas/{id}/                 # Atualizar
DELETE /api/v1/alertas/{id}/                 # Deletar
POST   /api/v1/alertas/{id}/marcar_lido/     # Marcar como lido
POST   /api/v1/alertas/{id}/marcar_resolvido/  # Marcar como resolvido
POST   /api/v1/alertas/marcar_todos_lidos/   # Marcar todos como lidos

Filtros:
?lido=false
?resolvido=false
?tipo=pendencia
?severidade=critico
```

## Logs de Auditoria

```http
GET    /api/v1/logs-auditoria/               # Listar logs (somente leitura)
GET    /api/v1/logs-auditoria/{id}/          # Detalhes do log

Filtros:
?usuario_id={uuid}
?acao=login
?data_inicio=2025-01-01
?data_fim=2025-12-31
```

## Códigos de Status HTTP

- `200 OK` - Requisição bem-sucedida
- `201 Created` - Recurso criado com sucesso
- `204 No Content` - Requisição bem-sucedida sem conteúdo de retorno
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - Não autenticado
- `403 Forbidden` - Sem permissão
- `404 Not Found` - Recurso não encontrado
- `500 Internal Server Error` - Erro no servidor

## Paginação

Todos os endpoints de listagem suportam paginação:

```http
GET /api/v1/empresas/?page=2&page_size=50
```

## Formato de Resposta

### Sucesso
```json
{
  "id": "uuid",
  "field1": "value1",
  "field2": "value2"
}
```

### Erro
```json
{
  "detail": "Mensagem de erro"
}
```

ou

```json
{
  "field_name": ["Mensagem de erro do campo"]
}
```

## Próximos Passos

- Implementar autenticação JWT para profissionais (login via CPF)
- Adicionar Celery tasks para processamento assíncrono
- Implementar processamento de Excel para importação em massa
- Criar sistema de envio de emails com templates
- Implementar geração de relatórios em PDF/Excel
- Adicionar geração de preview de cartões
- Criar sistema de cache com Redis
