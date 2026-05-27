# Importação de Profissionais via Excel

## Formato do Arquivo

O arquivo Excel deve conter as seguintes colunas na primeira linha (cabeçalho):

| Coluna A | Coluna B | Coluna C |
|----------|----------|----------|
| Nome     | CPF      | Email    |

### Detalhes dos Campos

1. **Nome** (obrigatório)
   - Nome completo do profissional
   - Exemplo: "João da Silva"

2. **CPF** (obrigatório)
   - CPF do profissional
   - Pode ser com ou sem pontuação
   - Exemplos: "12345678900" ou "123.456.789-00"
   - **Importante**: Deve ser único no sistema

3. **Email** (opcional)
   - Email do profissional
   - Se não fornecido, será gerado um email temporário único
   - Exemplo: "joao.silva@empresa.com"

## Exemplo de Arquivo

```
Nome                    | CPF             | Email
João da Silva          | 123.456.789-00  | joao.silva@empresa.com
Maria Santos           | 98765432100     | maria.santos@empresa.com
Pedro Oliveira         | 111.222.333-44  |
Ana Costa              | 555.666.777-88  | ana.costa@empresa.com
```

## Regras de Importação

### Senha Padrão
- A senha padrão de cada profissional são os **últimos 4 dígitos do CPF**
- Exemplo: CPF `123.456.789-00` → Senha: `7900`

### Email Temporário
- Se o email não for fornecido, o sistema gera automaticamente no formato:
  - `profissional_{CPF}_{codigo-unico}@clickid.temp`
- Exemplo: `profissional_12345678900_a1b2c3d4@clickid.temp`

### Validações
1. **CPF Duplicado**: Se o CPF já estiver cadastrado, a linha será ignorada com erro
2. **Nome ou CPF vazio**: Linhas sem nome ou CPF serão ignoradas com erro
3. **Email duplicado**: Se o email já existir, será adicionado um sufixo único

## Processo de Importação

### Transações Individuais
- Cada profissional é importado em uma transação separada
- Se um profissional falhar, os outros continuam sendo importados
- Isso evita que um erro bloqueie toda a importação

### Resultado da Importação

Após a importação, você receberá:

```json
{
  "total_importados": 3,
  "total_erros": 1,
  "importados": [
    {"linha": 2, "nome": "João da Silva", "cpf": "12345678900"},
    {"linha": 3, "nome": "Maria Santos", "cpf": "98765432100"},
    {"linha": 5, "nome": "Ana Costa", "cpf": "55566677788"}
  ],
  "erros": [
    {"linha": 4, "erro": "CPF 11122233344 já cadastrado"}
  ]
}
```

## Auditoria

Todas as importações são registradas no sistema de auditoria com:
- Usuário que realizou a importação
- Data e hora
- Total de profissionais importados
- Total de erros
- Nome do arquivo importado

## Problemas Comuns

### "Database is locked"
**Solução implementada**: Cada profissional é importado em sua própria transação, evitando lock prolongado do banco de dados.

### "Email já cadastrado"
**Solução implementada**: Se o email fornecido já existir, o sistema adiciona um código único automaticamente.

### "CPF já cadastrado"
**Comportamento**: A linha é ignorada e adicionada aos erros. Não é possível importar o mesmo CPF duas vezes.

## Exemplo de Template Excel

Um arquivo de exemplo pode ser baixado em: `/static/templates/importacao_profissionais_template.xlsx`

Ou crie manualmente:
1. Abra o Excel
2. Na linha 1 (cabeçalho), adicione: `Nome`, `CPF`, `Email`
3. A partir da linha 2, adicione os dados dos profissionais
4. Salve como `.xlsx`
5. Importe através do sistema

## Notas Técnicas

- **Formato suportado**: `.xlsx` (Excel 2007+)
- **Limite de linhas**: Sem limite técnico, mas recomendado até 1000 profissionais por importação
- **Tempo de processamento**: ~1-2 segundos por profissional
- **Codificação**: UTF-8 (suporta acentos e caracteres especiais)
