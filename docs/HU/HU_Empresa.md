# Histórias de Usuário - EMPRESA

## 🏢 Sistema de Coleta de Dados Multimídia - ClickID

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E001 |
| **Título** | Acessar Portal da Empresa |
| **Descrição** | Como **Representante da Empresa** <br> Quero **acessar o portal personalizado da minha empresa** <br> Para que **eu possa gerenciar coletas dos profissionais** |
| **Contexto / Observações** | - Cada empresa tem URL personalizada <br> - Login com credenciais específicas da empresa <br> - Interface personalizada com logo da empresa <br> - Multi-tenancy com isolamento de dados |
| **Cenários** | 1. **ACESSO VÁLIDO** <br> Dado que acesso URL da minha empresa (ex: minhaempresa.clickid.com.br) <br> Quando inserir credenciais corretas <br> Então devo acessar o painel da empresa <br><br> 2. **URL INEXISTENTE** <br> Dado que acesso URL não cadastrada <br> Quando tentar carregar página <br> Então deve exibir "Empresa não encontrada" <br><br> 3. **EMPRESA DESATIVADA** <br> Dado que empresa foi desativada pelo gerente <br> Quando tentar acessar <br> Então deve exibir "Acesso temporariamente suspenso" |
| **Critérios de Aceitação** | - URL única por empresa <br> - Branding (logo, cores) da empresa na interface <br> - Isolamento total de dados entre empresas <br> - Logs de acesso registrados <br> - Sessão segura com JWT |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E002 |
| **Título** | Realizar Login no Portal |
| **Descrição** | Como **Representante da Empresa** <br> Quero **fazer login com minhas credenciais** <br> Para que **eu possa acessar funcionalidades da empresa** |
| **Contexto / Observações** | - Credenciais fornecidas pelo gerente <br> - Autenticação JWT <br> - Possibilidade de recuperar senha |
| **Cenários** | 1. **LOGIN VÁLIDO** <br> Dado que insiro email e senha corretos <br> Quando clicar em "Entrar" <br> Então devo ser redirecionado para dashboard da empresa <br><br> 2. **CREDENCIAIS INVÁLIDAS** <br> Dado que insiro senha incorreta <br> Quando tentar logar <br> Então deve exibir "Email ou senha inválidos" <br><br> 3. **RECUPERAR SENHA** <br> Dado que esqueci minha senha <br> Quando clicar em "Esqueci minha senha" <br> Então devo receber email com link de redefinição |
| **Critérios de Aceitação** | - Validação de credenciais no backend <br> - Token JWT gerado com validade <br> - Limite de tentativas (5x) <br> - Recuperação de senha funcional <br> - Logs de acesso |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E003 |
| **Título** | Visualizar Coletas da Empresa |
| **Descrição** | Como **Representante da Empresa** <br> Quero **ver lista de todas as coletas da minha empresa** <br> Para que **eu possa acompanhar status e progresso** |
| **Contexto / Observações** | - Lista mostra coletas ativas e finalizadas <br> - Filtros por status e período <br> - Percentual de conclusão em tempo real |
| **Cenários** | 1. **LISTAR COLETAS** <br> Dado que acesso dashboard <br> Quando a página carregar <br> Então devo ver lista com todas as minhas coletas <br><br> 2. **FILTRAR POR STATUS** <br> Dado que seleciono filtro "Em Andamento" <br> Quando aplicar filtro <br> Então deve mostrar apenas coletas ativas <br><br> 3. **VER DETALHES DA COLETA** <br> Dado que clico em uma coleta <br> Quando acessar detalhes <br> Então devo ver progresso completo e lista de profissionais |
| **Critérios de Aceitação** | - Lista paginada para performance <br> - Percentual de conclusão calculado automaticamente <br> - Filtros: Em Andamento, Concluída, Cancelada <br> - Busca por nome da coleta ou data <br> - Interface responsiva |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E004 |
| **Título** | Cadastrar Profissionais Manualmente |
| **Descrição** | Como **Representante da Empresa** <br> Quero **cadastrar profissionais individualmente** <br> Para que **eles possam participar de coletas** |
| **Contexto / Observações** | - Empresas podem cadastrar seus profissionais <br> - CPF deve ser validado <br> - Senha padrão: 4 últimos dígitos do CPF |
| **Cenários** | 1. **CADASTRO VÁLIDO** <br> Dado que preencho CPF, nome e email do profissional <br> Quando clicar em "Cadastrar" <br> Então profissional deve ser criado e receber email <br><br> 2. **CPF INVÁLIDO** <br> Dado que insiro CPF com formato incorreto <br> Quando tentar cadastrar <br> Então deve exibir "CPF inválido" <br><br> 3. **PROFISSIONAL JÁ CADASTRADO** <br> Dado que CPF já existe na minha empresa <br> Quando tentar cadastrar <br> Então deve exibir "Profissional já cadastrado" |
| **Critérios de Aceitação** | - Validação de CPF com dígito verificador <br> - Email com formato válido <br> - Senha padrão: últimos 4 dígitos do CPF <br> - Email de notificação enviado <br> - Profissional vinculado à empresa |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E004A |
| **Título** | Importar Profissionais via Excel |
| **Descrição** | Como **Representante da Empresa** <br> Quero **importar lista de profissionais via arquivo Excel** <br> Para que **eu possa cadastrar múltiplos funcionários rapidamente** |
| **Contexto / Observações** | - Importação em lote via arquivo Excel <br> - Colunas obrigatórias: CPF e Nome <br> - Validação de todos os CPFs antes de processar <br> - Profissionais duplicados são identificados |
| **Cenários** | 1. **IMPORTAÇÃO VÁLIDA** <br> Dado que faço upload de Excel com CPF e Nome <br> Quando clicar em "Importar" <br> Então todos os profissionais devem ser cadastrados com sucesso <br><br> 2. **EXCEL COM ERROS** <br> Dado que arquivo contém CPFs inválidos <br> Quando processar importação <br> Então deve exibir relatório com erros por linha <br><br> 3. **CPFS DUPLICADOS** <br> Dado que Excel contém CPFs já cadastrados <br> Quando processar <br> Então deve ignorar duplicados e cadastrar apenas novos |
| **Critérios de Aceitação** | - Template Excel disponível para download <br> - Validação completa antes de salvar <br> - Relatório de sucesso/erros após importação <br> - CPFs duplicados identificados sem erro <br> - Emails enviados em lote para novos profissionais |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E005 |
| **Título** | Visualizar Lista de Profissionais |
| **Descrição** | Como **Representante da Empresa** <br> Quero **ver todos os profissionais da minha empresa** <br> Para que **eu possa gerenciar e acompanhar status** |
| **Contexto / Observações** | - Lista todos profissionais vinculados <br> - Status de cada coleta por profissional <br> - Possibilidade de filtrar e buscar <br> - Organização por departamentos |
| **Cenários** | 1. **LISTAR PROFISSIONAIS** <br> Dado que acesso aba "Profissionais" <br> Quando a página carregar <br> Então devo ver lista completa com status e departamento <br><br> 2. **FILTRAR POR STATUS** <br> Dado que seleciono "Pendentes" <br> Quando aplicar filtro <br> Então deve mostrar apenas profissionais com coletas não finalizadas <br><br> 3. **BUSCAR PROFISSIONAL** <br> Dado que digito CPF ou nome na busca <br> Quando pesquisar <br> Então deve filtrar resultados em tempo real |
| **Critérios de Aceitação** | - Lista paginada com: nome, CPF, departamento, status <br> - Status atualizado em tempo real <br> - Filtros: Todos, Pendentes, Concluídos, por Departamento <br> - Busca por nome ou CPF funcional <br> - Performance otimizada |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E005A |
| **Título** | Organizar Profissionais em Departamentos |
| **Descrição** | Como **Representante da Empresa** <br> Quero **organizar profissionais em departamentos** <br> Para que **eu possa gerenciar equipes de forma estruturada** |
| **Contexto / Observações** | - Departamentos funcionam como "pastas" organizacionais <br> - Profissional pode pertencer a apenas um departamento <br> - Departamentos facilitam início de coletas segmentadas |
| **Cenários** | 1. **CRIAR DEPARTAMENTO** <br> Dado que acesso "Gerenciar Departamentos" <br> Quando criar novo departamento (ex: "RH", "TI", "Operacional") <br> Então departamento deve ficar disponível para vinculação <br><br> 2. **VINCULAR PROFISSIONAL** <br> Dado que seleciono profissional <br> Quando escolher departamento no dropdown <br> Então profissional deve ser movido para esse departamento <br><br> 3. **VISUALIZAR POR DEPARTAMENTO** <br> Dado que filtro por "Departamento TI" <br> Quando aplicar filtro <br> Então deve listar apenas profissionais desse departamento |
| **Critérios de Aceitação** | - CRUD completo de departamentos <br> - Vinculação individual ou em lote <br> - Visualização hierárquica (departamento > profissionais) <br> - Filtros por departamento funcionais <br> - Contadores de profissionais por departamento |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E005B |
| **Título** | Iniciar Coleta Segmentada |
| **Descrição** | Como **Representante da Empresa** <br> Quero **iniciar coletas para grupos específicos de profissionais** <br> Para que **eu possa fazer coletas direcionadas** |
| **Contexto / Observações** | - Coletas podem ser para: toda empresa, departamentos específicos ou profissionais selecionados <br> - Múltiplos departamentos podem ser selecionados <br> - Seleção manual permite escolher profissionais individualmente |
| **Cenários** | 1. **COLETA PARA TODA EMPRESA** <br> Dado que seleciono opção "Toda Empresa" <br> Quando iniciar coleta <br> Então todos os profissionais ativos devem ser incluídos <br><br> 2. **COLETA POR DEPARTAMENTO** <br> Dado que seleciono departamentos "RH" e "TI" <br> Quando iniciar coleta <br> Então apenas profissionais desses departamentos devem ser incluídos <br><br> 3. **COLETA PARA PROFISSIONAIS ESPECÍFICOS** <br> Dado que seleciono manualmente 5 profissionais <br> Quando iniciar coleta <br> Então apenas os selecionados devem receber formulário |
| **Critérios de Aceitação** | - Opções: Toda Empresa / Por Departamento / Seleção Manual <br> - Seleção múltipla de departamentos <br> - Checkbox para seleção individual de profissionais <br> - Preview de quantos profissionais serão incluídos <br> - Confirmação antes de iniciar coleta |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E006 |
| **Título** | Baixar Relatório de Coleta |
| **Descrição** | Como **Representante da Empresa** <br> Quero **baixar dados de uma coleta em Excel** <br> Para que **eu possa analisar informações dos profissionais** |
| **Contexto / Observações** | - Relatórios em formato Excel <br> - Opções: todos, apenas pendentes, apenas concluídos <br> - Dados textuais (sem mídias) |
| **Cenários** | 1. **BAIXAR TODOS OS DADOS** <br> Dado que estou nos detalhes da coleta <br> Quando clicar em "Baixar Todos (Excel)" <br> Então deve gerar Excel com todos os profissionais <br><br> 2. **BAIXAR APENAS PENDENTES** <br> Dado que seleciono filtro "Pendentes" <br> Quando clicar em "Baixar Pendentes" <br> Então Excel deve conter apenas CPFs não finalizados <br><br> 3. **BAIXAR APENAS CONCLUÍDOS** <br> Dado que seleciono filtro "Concluídos" <br> Quando clicar em "Baixar Concluídos" <br> Então Excel deve conter apenas profissionais que finalizaram |
| **Critérios de Aceitação** | - Excel formatado e padronizado <br> - Colunas: CPF, Nome, Status, Data Conclusão, Dados do Formulário <br> - Exclusão de mídias (fotos e assinaturas) <br> - Downloads assíncronos <br> - Notificação quando pronto |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E007 |
| **Título** | Baixar Mídias da Coleta |
| **Descrição** | Como **Representante da Empresa** <br> Quero **baixar fotos e assinaturas separadamente** <br> Para que **eu possa processar imagens dos profissionais** |
| **Contexto / Observações** | - Download em formato ZIP <br> - Organização por CPF em pastas <br> - Downloads separados (fotos / assinaturas) |
| **Cenários** | 1. **BAIXAR FOTOS** <br> Dado que coleta possui fotos <br> Quando clicar em "Baixar Fotos" <br> Então deve gerar ZIP com fotos organizadas por CPF <br><br> 2. **BAIXAR ASSINATURAS** <br> Dado que coleta possui assinaturas <br> Quando clicar em "Baixar Assinaturas" <br> Então deve gerar ZIP com assinaturas organizadas por CPF <br><br> 3. **COLETA SEM MÍDIAS** <br> Dado que coleta não inclui fotos/assinaturas <br> Quando tentar baixar mídias <br> Então botão deve estar desabilitado |
| **Critérios de Aceitação** | - ZIP organizado: CPF_nome/foto.jpg <br> - ZIP organizado: CPF_nome/assinatura.png <br> - Apenas mídias de profissionais concluídos <br> - Download assíncrono com notificação <br> - Validação de existência de mídias |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E008 |
| **Título** | Reenviar Notificação para Profissional |
| **Descrição** | Como **Representante da Empresa** <br> Quero **reenviar email de notificação** <br> Para que **profissional receba novamente link de acesso** |
| **Contexto / Observações** | - Útil quando profissional não recebeu email <br> - Histórico de envios deve ser registrado <br> - Limite de reenvios por período |
| **Cenários** | 1. **REENVIAR PARA UM PROFISSIONAL** <br> Dado que seleciono profissional pendente <br> Quando clicar em "Reenviar Notificação" <br> Então novo email deve ser enviado com link <br><br> 2. **REENVIO EM LOTE** <br> Dado que seleciono múltiplos profissionais pendentes <br> Quando clicar em "Reenviar para Selecionados" <br> Então emails devem ser enviados para todos <br><br> 3. **LIMITE DE REENVIOS** <br> Dado que já reenviei 3x em 24h <br> Quando tentar reenviar novamente <br> Então deve exibir "Limite de reenvios atingido" |
| **Critérios de Aceitação** | - Email com link direto para formulário <br> - Histórico de envios visível <br> - Limite: 3 reenvios por 24h por profissional <br> - Confirmação de envio com mensagem <br> - Logs registrados |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E009 |
| **Título** | Visualizar Dashboard da Empresa |
| **Descrição** | Como **Representante da Empresa** <br> Quero **ver métricas gerais da minha empresa** <br> Para que **eu possa ter visão consolidada** |
| **Contexto / Observações** | - Dashboard com KPIs principais <br> - Coletas ativas vs concluídas <br> - Total de profissionais cadastrados |
| **Cenários** | 1. **VISUALIZAR CARDS** <br> Dado que acesso página inicial <br> Quando dashboard carregar <br> Então devo ver: total de coletas, coletas ativas, profissionais cadastrados, taxa de conclusão média <br><br> 2. **VISUALIZAR GRÁFICO DE PROGRESSO** <br> Dado que estou na dashboard <br> Quando rolar página <br> Então devo ver gráfico de evolução de coletas por mês <br><br> 3. **ACESSAR COLETA RÁPIDA** <br> Dado que clico em card "Coletas Ativas" <br> Quando clicar <br> Então devo ser redirecionado para lista filtrada |
| **Critérios de Aceitação** | - Cards com números atualizados <br> - Gráfico de evolução mensal <br> - Taxa de conclusão calculada automaticamente <br> - Links rápidos para seções <br> - Interface limpa e intuitiva |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-E010 |
| **Título** | Editar Dados da Empresa |
| **Descrição** | Como **Representante da Empresa** <br> Quero **atualizar dados cadastrais da empresa** <br> Para que **informações estejam sempre corretas** |
| **Contexto / Observações** | - Dados editáveis: endereço, telefone, email, logo <br> - Dados não editáveis: CNPJ, razão social (apenas gerente) <br> - Validações aplicáveis |
| **Cenários** | 1. **EDITAR DADOS** <br> Dado que acesso "Configurações da Empresa" <br> Quando alterar telefone e email <br> Então as alterações devem ser salvas <br><br> 2. **ATUALIZAR LOGO** <br> Dado que faço upload de nova logo <br> Quando salvar <br> Então logo deve aparecer em todo portal <br><br> 3. **VALIDAÇÃO DE CAMPOS** <br> Dado que insiro email inválido <br> Quando tentar salvar <br> Então deve exibir erro de validação |
| **Critérios de Aceitação** | - Campos editáveis funcionais <br> - Upload de logo (formatos: PNG, JPG, SVG) <br> - Validação de email e telefone <br> - Confirmação de salvamento <br> - Log de alterações |
