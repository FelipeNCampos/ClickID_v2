# Prompt Templates - ClickID v2.0

Este arquivo contém templates de prompts para auxiliar na padronização de solicitações ao GitHub Copilot durante o desenvolvimento do projeto ClickID v2.0.

## 1. Criar Novo Model

```
Crie um novo model Django chamado [NOME_MODEL] no app [NOME_APP] com os seguintes campos:
- [campo1]: [tipo] ([obrigatório/opcional])
- [campo2]: [tipo] ([obrigatório/opcional])
...

Requisitos:
- Use UUID como chave primária
- Inclua timestamps (criado_em, atualizado_em)
- Adicione campo is_active para soft delete
- Siga as convenções de nomenclatura do projeto
- Inclua docstring explicativa
- Adicione Meta class com verbose_name e ordering
```

**Exemplo:**
```
Crie um novo model Django chamado Departamento no app empresas com os seguintes campos:
- nome: CharField max 100 (obrigatório)
- descricao: TextField (opcional)
- empresa: ForeignKey para Empresa (obrigatório)

Requisitos:
- Use UUID como chave primária
- Inclua timestamps (criado_em, atualizado_em)
- Adicione campo is_active para soft delete
- Siga as convenções de nomenclatura do projeto
- Inclua docstring explicativa
- Adicione Meta class com verbose_name e ordering
```

## 2. Criar ViewSet com Actions

```
Crie um ViewSet para o model [NOME_MODEL] no app [NOME_APP] com:
- CRUD completo (list, create, retrieve, update, delete)
- Filtro por [campo_filtro]
- Permission: [tipo_permissao]

Actions customizadas:
- [nome_action]: [descrição e método HTTP]
...

Cada action deve:
- Incluir docstring
- Registrar auditoria se ação crítica
- Retornar Response adequado
- Tratar exceções
```

**Exemplo:**
```
Crie um ViewSet para o model Coleta no app coletas com:
- CRUD completo (list, create, retrieve, update, delete)
- Filtro por empresa
- Permission: IsAuthenticated

Actions customizadas:
- iniciar: Iniciar uma coleta (POST)
- cancelar: Cancelar uma coleta (POST)
- adicionar_profissionais: Adicionar profissionais (POST)

Cada action deve:
- Incluir docstring
- Registrar auditoria se ação crítica
- Retornar Response adequado
- Tratar exceções
```

## 3. Criar Template Django

```
Crie um template Django em [caminho] para [propósito]:

Estrutura:
- Extend base.html
- Breadcrumb: [navegação]
- Card principal com [conteúdo]
- [Componentes adicionais]

Componentes Bootstrap:
- [Card/Table/Form/Modal/etc]

JavaScript:
- [Funcionalidades necessárias]

Siga padrões:
- Use Bootstrap 5.3
- Bootstrap Icons para ícones
- Classes de nomenclatura do projeto
- Formatação de datas em pt-BR
```

**Exemplo:**
```
Crie um template Django em templates/empresas/coleta_detail.html para exibir detalhes de uma coleta:

Estrutura:
- Extend base.html
- Breadcrumb: Dashboard > Coletas > [Nome da Coleta]
- Card principal com informações da coleta
- Sidebar com estatísticas
- Lista de profissionais em tabela

Componentes Bootstrap:
- Cards para informações e estatísticas
- Table responsiva para profissionais
- Progress bar para percentual de conclusão
- Badges para status

JavaScript:
- Formatação de datas ISO para dd/mm/yyyy
- Filtro de profissionais por status

Siga padrões:
- Use Bootstrap 5.3
- Bootstrap Icons para ícones
- Classes de nomenclatura do projeto
- Formatação de datas em pt-BR
```

## 4. Criar Proxy View

```
Crie uma proxy view em [app]/web_views.py chamada [nome_view]:

Propósito: [descrição]
Método HTTP: [GET/POST]
Endpoint API: [URL da API]
Template: [caminho do template]
Redirect em erro: [URL de redirect]

Decorator: @empresa_required

Se exportação de arquivo:
- Content-Type: [tipo]
- Nome do arquivo: [padrão]
- Stream: True/False
```

**Exemplo:**
```
Crie uma proxy view em empresas/web_views.py chamada coleta_exportar_excel:

Propósito: Exportar dados de uma coleta para Excel
Método HTTP: GET
Endpoint API: /api/v1/coletas/{pk}/exportar_excel/
Template: N/A (retorna arquivo)
Redirect em erro: web-empresa:coleta-detail

Decorator: @empresa_required

Se exportação de arquivo:
- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Nome do arquivo: Pegar do Content-Disposition da API
- Stream: True
```

## 5. Adicionar Auditoria

```
Adicione registro de auditoria na action [nome_action] do ViewSet [nome_viewset]:

Tipo de ação: [TipoAcao enum]
Descrição: [template da descrição com variáveis]
Dados adicionais: [dict com campos relevantes]

Posição: Após [ação bem-sucedida]
Tratar exceção: Sim/Não
```

**Exemplo:**
```
Adicione registro de auditoria na action adicionar_profissionais do ViewSet ColetaViewSet:

Tipo de ação: TipoAcao.PARTICIPANTE_ADICIONADO
Descrição: "{quantidade} profissionais adicionados à coleta '{coleta.nome}'"
Dados adicionais: {
    'quantidade': len(profissionais_adicionados),
    'todos_profissionais': todos_profissionais
}

Posição: Após profissionais serem adicionados com sucesso
Tratar exceção: Sim (try/except para Empresa.DoesNotExist)
```

## 6. Criar Exportação

```
Crie uma action de exportação em [ViewSet] para exportar [dados]:

Formato: [Excel/CSV/ZIP/PDF]
Biblioteca: [openpyxl/csv/zipfile/reportlab]
Nome arquivo: [padrão com timestamp]

Estrutura do arquivo:
- [Seção 1: descrição]
- [Seção 2: descrição]
...

Incluir:
- Timestamp de geração
- Informações da empresa
- [Outros metadados]

Estilização (se Excel):
- Headers: [cores, fonte]
- Colunas: [larguras]
```

**Exemplo:**
```
Crie uma action de exportação em ColetaViewSet para exportar dados textuais de respostas:

Formato: Excel
Biblioteca: openpyxl
Nome arquivo: coleta_{nome}_{timestamp}.xlsx

Estrutura do arquivo:
- Linha 1: "Dados da Coleta"
- Linhas 3-10: Informações da coleta (nome, empresa, status, etc)
- Linha 11: "Gerado em: dd/mm/yyyy HH:MM:SS"
- Linha 13+: Tabela com CPF, Nome e campos dinâmicos do modelo

Incluir:
- Timestamp de geração
- Informações da empresa
- Total de respostas

Estilização (se Excel):
- Headers: Azul (#0066CC), fonte branca, bold
- Colunas: Auto-ajustar largura
```

## 7. Criar Migrations

```
Crie migrations para o app [nome_app]:

Alterações:
- [Alteração 1: descrição]
- [Alteração 2: descrição]
...

Comando: python manage.py makemigrations [app_name]
Depois aplicar: python manage.py migrate [app_name]

Verificar:
- Dependências de outras migrations
- Data migrations se necessário
- Reverse migrations
```

**Exemplo:**
```
Crie migrations para o app auditoria:

Alterações:
- Criar model LogAuditoria com todos os campos
- Adicionar índices em data_hora e empresa
- Adicionar choices para tipo_acao

Comando: python manage.py makemigrations auditoria
Depois aplicar: python manage.py migrate auditoria

Verificar:
- Dependências de usuarios e empresas migrations
- Sem data migrations necessárias
- Reverse migrations OK
```

## 8. Adicionar Validação

```
Adicione validação no model/serializer [nome]:

Validações:
- [Campo]: [regra de validação]
...

Tipo: Clean method / Validator / Serializer validation
Mensagem de erro: [mensagem em português]
Quando validar: [momento da validação]
```

**Exemplo:**
```
Adicione validação no model Coleta:

Validações:
- data_inicio: Não pode ser no passado
- status: Apenas rascunho pode ser iniciado
- profissionais: Mínimo de 1 profissional para iniciar

Tipo: Clean method no model
Mensagem de erro: Mensagens claras em português
Quando validar: Antes de save()
```

## 9. Refatorar Código

```
Refatore o código em [arquivo] [função/classe]:

Problemas atuais:
- [Problema 1]
- [Problema 2]
...

Melhorias desejadas:
- [Melhoria 1]
- [Melhoria 2]
...

Manter:
- [Funcionalidade 1 a manter]
- [Funcionalidade 2 a manter]

Padrões: Seguir convenções do projeto
Testes: Garantir que testes continuam passando
```

**Exemplo:**
```
Refatore o código em coletas/views.py função adicionar_profissionais:

Problemas atuais:
- Código muito longo (150+ linhas)
- Muita lógica aninhada
- Difícil de testar

Melhorias desejadas:
- Extrair lógica em métodos privados
- Reduzir complexidade ciclomática
- Separar validação de execução

Manter:
- Registro de auditoria
- Tratamento de erros
- Response format

Padrões: Seguir convenções do projeto
Testes: Garantir que testes continuam passando
```

## 10. Corrigir Bug

```
Corrija o bug em [arquivo] [função/classe]:

Descrição do bug:
[Descrição clara do problema]

Comportamento atual:
[O que está acontecendo]

Comportamento esperado:
[O que deveria acontecer]

Erro específico (se aplicável):
[Mensagem de erro]

Causa provável:
[Hipótese sobre a causa]

Solução proposta:
[Como corrigir]

Testes:
[Como verificar se foi corrigido]
```

**Exemplo:**
```
Corrija o bug em coletas/views.py função adicionar_profissionais:

Descrição do bug:
Erro ao adicionar profissionais individualmente a uma coleta

Comportamento atual:
FieldError: Cannot resolve keyword 'id' into field

Comportamento esperado:
Profissionais devem ser adicionados sem erro

Erro específico:
django.core.exceptions.FieldError: Cannot resolve keyword 'id' into field. Choices are: ... usuario, usuario_id

Causa provável:
Model Profissional usa 'usuario' como PK (OneToOneField), não tem campo 'id'

Solução proposta:
Trocar Profissional.objects.filter(id__in=ids) por Profissional.objects.filter(usuario__in=ids)

Testes:
Testar adicionando profissionais individuais e "todos profissionais"
```

## Uso dos Templates

Para usar estes templates:
1. Copie o template adequado
2. Preencha os placeholders [EM_MAIÚSCULAS]
3. Adicione detalhes específicos do seu caso
4. Cole no chat com o GitHub Copilot

Os templates garantem:
- Contexto completo para o Copilot
- Consistência nas solicitações
- Aderência aos padrões do projeto
- Menos iterações até o resultado desejado
