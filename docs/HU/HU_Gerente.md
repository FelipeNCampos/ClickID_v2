# Histórias de Usuário - GERENTE

## 🎯 Sistema de Coleta de Dados Multimídia - ClickID

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G001 |
| **Título** | Realizar Login como Gerente |
| **Descrição** | Como **Gerente** <br> Quero **fazer login no sistema** <br> Para que **eu possa acessar o painel administrativo** |
| **Contexto / Observações** | - Login deve ser seguro com autenticação JWT <br> - Sessão deve expirar após período de inatividade <br> - Logs de acesso devem ser registrados |
| **Cenários** | 1. **LOGIN VÁLIDO** <br> Dado que insiro credenciais corretas <br> Quando clicar em "Entrar" <br> Então devo ser redirecionado para o dashboard <br><br> 2. **LOGIN INVÁLIDO** <br> Dado que insiro credenciais incorretas <br> Quando clicar em "Entrar" <br> Então deve exibir "Credenciais inválidas" <br><br> 3. **CONTA BLOQUEADA** <br> Dado que erro a senha 5 vezes <br> Quando tentar logar novamente <br> Então a conta deve ser temporariamente bloqueada |
| **Critérios de Aceitação** | - Sistema deve validar credenciais no backend <br> - Token JWT deve ser gerado para sessões válidas <br> - Mensagens de erro devem ser claras e seguras <br> - Logs de tentativas de login devem ser registrados |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G002 |
| **Título** | Cadastrar Novo Gerente |
| **Descrição** | Como **Gerente** <br> Quero **cadastrar outros gerentes** <br> Para que **eles possam ter acesso às funcionalidades de administração** |
| **Contexto / Observações** | - Apenas gerentes podem cadastrar outros gerentes <br> - CPF deve ser validado <br> - Email com credenciais deve ser enviado |
| **Cenários** | 1. **CADASTRO VÁLIDO** <br> Dado que preencho dados corretos do gerente <br> Quando clicar em "Cadastrar" <br> Então o gerente deve ser criado e receber email <br><br> 2. **CPF INVÁLIDO** <br> Dado que insiro CPF inválido <br> Quando tentar cadastrar <br> Então deve exibir "CPF inválido" <br><br> 3. **GERENTE DUPLICADO** <br> Dado que CPF já existe no sistema <br> Quando tentar cadastrar <br> Então deve exibir "Gerente já cadastrado" |
| **Critérios de Aceitação** | - CPF deve ser validado com dígito verificador <br> - Email deve ter formato válido <br> - Senha temporária deve ser gerada automaticamente <br> - Email de boas-vindas deve ser enviado |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G003 |
| **Título** | Cadastrar Nova Empresa |
| **Descrição** | Como **Gerente** <br> Quero **cadastrar uma nova empresa** <br> Para que **ela possa usar o sistema de coletas** |
| **Contexto / Observações** | - Apenas gerentes podem cadastrar empresas <br> - CNPJ deve ser validado <br> - Empresa inicia com status "Ativa" <br> - URL personalizada deve ser gerada |
| **Cenários** | 1. **CADASTRO VÁLIDO** <br> Dado que preencho dados corretos da empresa <br> Quando clicar em "Cadastrar" <br> Então a empresa deve ser criada com URL personalizada <br><br> 2. **CNPJ INVÁLIDO** <br> Dado que insiro CNPJ inválido <br> Quando tentar cadastrar <br> Então deve exibir "CNPJ inválido" <br><br> 3. **EMPRESA DUPLICADA** <br> Dado que CNPJ já existe no sistema <br> Quando tentar cadastrar <br> Então deve exibir "Empresa já cadastrada" |
| **Critérios de Aceitação** | - CNPJ deve ser validado com dígito verificador <br> - Razão social é obrigatória <br> - Email deve ter formato válido <br> - Sistema deve gerar URL personalizada (ex: empresa.clickid.com.br) <br> - Logo da empresa pode ser enviada (opcional) |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G004 |
| **Título** | Visualizar Dashboard Analítica |
| **Descrição** | Como **Gerente** <br> Quero **visualizar dashboard com métricas do sistema** <br> Para que **eu possa acompanhar o desempenho global** |
| **Contexto / Observações** | - Dashboard deve atualizar em tempo real <br> - Gráficos devem ser interativos <br> - Filtros por período (1-30 dias, mês anterior) |
| **Cenários** | 1. **VISUALIZAR CARDS PRINCIPAIS** <br> Dado que acesso o dashboard <br> Quando a página carregar <br> Então devo ver cards: coletas em aberto, concluídas, empresas ativas, coletas pendentes do mês <br><br> 2. **VISUALIZAR CARDS COMPARATIVOS** <br> Dado que estou na dashboard <br> Quando rolar a página <br> Então devo ver: coletas em aberto mês anterior, concluídas mês anterior, empresas desativadas <br><br> 3. **APLICAR FILTROS INTERATIVOS** <br> Dado que seleciono período específico <br> Quando aplicar filtro <br> Então gráficos devem atualizar com dados do período selecionado |
| **Critérios de Aceitação** | - Cards devem mostrar números em tempo real <br> - Gráficos de coletas iniciadas, canceladas, concluídas no mês <br> - Gráfico de coletas pendentes de meses passados <br> - Filtros interativos funcionais <br> - Performance otimizada |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G005 |
| **Título** | Gerenciar Lista de Empresas |
| **Descrição** | Como **Gerente** <br> Quero **listar e filtrar empresas cadastradas** <br> Para que **eu possa gerenciar todas as empresas do sistema** |
| **Contexto / Observações** | - Lista paginada de empresas <br> - Filtros por status (ativa/inativa) <br> - Ordenação por interações com sistema |
| **Cenários** | 1. **LISTAR EMPRESAS** <br> Dado que acesso aba "Empresas" <br> Quando a página carregar <br> Então devo ver lista com todas as empresas <br><br> 2. **FILTRAR POR STATUS** <br> Dado que seleciono filtro "Inativas" <br> Quando aplicar filtro <br> Então deve mostrar apenas empresas inativas <br><br> 3. **ORDENAR POR INTERAÇÕES** <br> Dado que seleciono ordenação por "Coletas Iniciadas" <br> Quando aplicar ordenação <br> Então lista deve reorganizar por quantidade de coletas |
| **Critérios de Aceitação** | - Lista paginada com busca por nome/CNPJ <br> - Filtros: ativa, inativa <br> - Ordenação: iniciar coleta, concluir coleta, cancelar coleta <br> - Performance otimizada para grandes volumes |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G006 |
| **Título** | Visualizar Perfil da Empresa |
| **Descrição** | Como **Gerente** <br> Quero **acessar perfil detalhado de uma empresa** <br> Para que **eu possa ver dados e histórico de coletas** |
| **Contexto / Observações** | - Acesso via clique na lista de empresas <br> - Dados da empresa devem ser editáveis <br> - Histórico completo de coletas |
| **Cenários** | 1. **ACESSAR PERFIL** <br> Dado que clico em uma empresa da lista <br> Quando a página carregar <br> Então devo ver dados completos e histórico de coletas <br><br> 2. **EDITAR DADOS** <br> Dado que estou no perfil da empresa <br> Quando alterar dados e salvar <br> Então as alterações devem ser persistidas <br><br> 3. **VISUALIZAR HISTÓRICO** <br> Dado que estou no perfil <br> Quando rolar para seção de histórico <br> Então devo ver lista completa de coletas (ativas e finalizadas) |
| **Critérios de Aceitação** | - Dados da empresa exibidos corretamente <br> - Edição de dados funcional <br> - Lista de histórico de coletas ordenada por data <br> - Status e percentual de conclusão visíveis |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G007 |
| **Título** | Criar Modelo de Cartão com Canvas |
| **Descrição** | Como **Gerente** <br> Quero **criar modelos de cartões em canvas drag-and-drop para cada empresa** <br> Para que **cada empresa tenha seus modelos personalizados privados** |
| **Contexto / Observações** | - Modelos são PRIVADOS por empresa <br> - Gerente acessa empresa para gerenciar seus modelos <br> - Canvas com dimensões reais do cartão (ex: 85mm x 54mm) <br> - Campos arrastados e posicionados visualmente <br> - Cada campo tem configurações visuais (fonte, cor, tamanho, posição) <br> - Pergunta do formulário configurada por campo |
| **Cenários** | 1. **CRIAR MODELO CANVAS** <br> Dado que acesso empresa e clico em "Modelos" <br> Quando criar novo modelo <br> Então devo ter canvas com dimensões reais do cartão <br><br> 2. **ADICIONAR CAMPO NO CANVAS** <br> Dado que estou no editor canvas <br> Quando arrastar campo "Nome" para o cartão <br> Então devo poder posicionar, redimensionar e estilizar (fonte, cor, tamanho) <br><br> 3. **CONFIGURAR PERGUNTA DO FORMULÁRIO** <br> Dado que adicionei campo "Nome" no cartão <br> Quando configurar propriedades <br> Então devo definir: "Pergunta: Nome do profissional", placeholder, obrigatoriedade |
| **Critérios de Aceitação** | - Canvas drag-and-drop funcional <br> - Dimensões reais do cartão (mm) <br> - Campos: texto, foto, assinatura, código barras, QR code <br> - Estilização: fonte, tamanho, cor, negrito, itálico, alinhamento <br> - Configuração de pergunta por campo <br> - Preview do cartão em tempo real <br> - Modelos privados por empresa |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G007A |
| **Título** | Acessar e Gerenciar Modelos da Empresa |
| **Descrição** | Como **Gerente** <br> Quero **acessar os modelos de uma empresa específica** <br> Para que **eu possa criar e gerenciar modelos privados dessa empresa** |
| **Contexto / Observações** | - Modelos são privados e isolados por empresa <br> - Gerente acessa perfil da empresa para ver/criar modelos <br> - Cada empresa tem sua própria biblioteca de modelos |
| **Cenários** | 1. **ACESSAR MODELOS DA EMPRESA** <br> Dado que estou no perfil de uma empresa <br> Quando clicar em aba "Modelos de Cartões" <br> Então devo ver apenas modelos dessa empresa <br><br> 2. **CRIAR NOVO MODELO PARA EMPRESA** <br> Dado que estou na aba de modelos da empresa <br> Quando clicar em "Novo Modelo" <br> Então devo abrir editor canvas para criar modelo exclusivo <br><br> 3. **EDITAR MODELO EXISTENTE** <br> Dado que seleciono modelo da empresa <br> Quando clicar em "Editar" <br> Então devo abrir canvas com modelo carregado |
| **Critérios de Aceitação** | - Lista de modelos filtrada por empresa <br> - Isolamento total entre empresas <br> - CRUD completo de modelos <br> - Ativação/desativação de modelos <br> - Indicação visual de modelo ativo |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G007B |
| **Título** | Configurar Campos Visuais e Formulário |
| **Descrição** | Como **Gerente** <br> Quero **configurar propriedades visuais do campo no cartão e sua pergunta no formulário** <br> Para que **o campo apareça formatado no cartão e gere pergunta correta no formulário** |
| **Contexto / Observações** | - Cada campo tem duas configurações: visual (cartão) e formulário <br> - Configuração visual: fonte, cor, tamanho, posição, alinhamento <br> - Configuração formulário: pergunta, placeholder, validação |
| **Cenários** | 1. **CONFIGURAR CAMPO "NOME"** <br> Dado que adicionei campo de texto no canvas <br> Quando abrir propriedades <br> Então devo configurar: <br> Visual: Fonte Arial, 18pt, cor preta, posição X:10mm Y:20mm <br> Formulário: "Nome completo do profissional", obrigatório <br><br> 2. **CAMPO COM VALIDAÇÃO** <br> Dado que adiciono campo "CPF" <br> Quando configurar <br> Então devo definir: tipo CPF, máscara automática, validação de dígitos <br><br> 3. **CAMPO DE FOTO** <br> Dado que adiciono campo foto <br> Quando configurar <br> Então devo definir: posição e tamanho no cartão, pergunta "Envie sua foto 3x4" |
| **Critérios de Aceitação** | - Painel de propriedades completo <br> - Preview em tempo real das mudanças <br> - Validação de posição (dentro do cartão) <br> - Biblioteca de fontes disponível <br> - Color picker para cores <br> - Pergunta gera campo correspondente no formulário |
| **Título** | Iniciar Coleta para Empresa |
| **Descrição** | Como **Gerente** <br> Quero **iniciar uma coleta de dados para uma empresa** <br> Para que **profissionais possam preencher formulários** |
| **Contexto / Observações** | - Coleta vinculada a modelo de cartão <br> - Importação via arquivo Excel (CPF e nomes) <br> - Profissionais cadastrados automaticamente <br> - Possibilidade de segmentar: toda empresa, departamentos ou profissionais específicos |
| **Cenários** | 1. **INICIAR COLETA COM EXCEL** <br> Dado que seleciono empresa e modelo <br> Quando importar Excel válido com CPFs e nomes <br> Então profissionais devem ser cadastrados e coleta iniciada <br><br> 2. **COLETA SEGMENTADA POR DEPARTAMENTO** <br> Dado que seleciono empresa e departamentos específicos <br> Quando iniciar coleta <br> Então apenas profissionais dos departamentos selecionados devem receber formulário <br><br> 3. **COLETA PARA PROFISSIONAIS ESPECÍFICOS** <br> Dado que seleciono manualmente profissionais da empresa <br> Quando iniciar coleta <br> Então apenas os selecionados devem ser incluídos |
| **Critérios de Aceitação** | - Validação de formato do Excel (CPF, Nome obrigatórios) <br> - CPFs validados com dígito verificador <br> - Opções de segmentação: Toda Empresa / Departamentos / Seleção Manual / Import Excel <br> - Profissionais cadastrados automaticamente (via Excel) <br> - Emails de notificação enviados <br> - Status da coleta: "Em Andamento" |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G009 |
| **Título** | Visualizar Detalhes de Coleta |
| **Descrição** | Como **Gerente** <br> Quero **acessar detalhes completos de uma coleta** <br> Para que **eu possa acompanhar progresso e resultados** |
| **Contexto / Observações** | - Acesso via perfil da empresa ou dashboard <br> - Status em tempo real <br> - Percentual de conclusão visível |
| **Cenários** | 1. **VISUALIZAR COLETA EM ANDAMENTO** <br> Dado que clico em coleta ativa <br> Quando a página carregar <br> Então devo ver status, percentual de conclusão e lista de profissionais <br><br> 2. **VISUALIZAR COLETA CONCLUÍDA** <br> Dado que clico em coleta finalizada <br> Quando acessar detalhes <br> Então devo ver resumo completo e opções de download <br><br> 3. **FILTRAR PROFISSIONAIS** <br> Dado que estou nos detalhes da coleta <br> Quando aplicar filtro "Pendentes" ou "Concluídos" <br> Então lista deve mostrar apenas profissionais do status selecionado |
| **Critérios de Aceitação** | - Status da coleta atualizado em tempo real <br> - Percentual calculado automaticamente <br> - Lista de profissionais com status individual <br> - Filtros funcionais (pendente/concluído) |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G010 |
| **Título** | Baixar Dados da Coleta |
| **Descrição** | Como **Gerente** <br> Quero **baixar dados de uma coleta** <br> Para que **eu possa analisar e processar informações** |
| **Contexto / Observações** | - Múltiplas opções de download <br> - Excel com dados (sem mídias) <br> - Download separado de fotos e assinaturas |
| **Cenários** | 1. **BAIXAR DADOS EM EXCEL** <br> Dado que estou nos detalhes da coleta <br> Quando clicar em "Baixar Respostas (Excel)" <br> Então deve gerar Excel com dados textuais (excluindo fotos e assinaturas) <br><br> 2. **BAIXAR FOTOS** <br> Dado que coleta possui fotos <br> Quando clicar em "Baixar Fotos" <br> Então deve gerar ZIP organizado por CPF <br><br> 3. **BAIXAR LISTA DE PENDENTES** <br> Dado que coleta tem profissionais pendentes <br> Quando clicar em "Baixar Pendentes" <br> Então deve gerar Excel apenas com CPFs não finalizados |
| **Critérios de Aceitação** | - Excel formatado e padronizado <br> - ZIP com fotos organizadas por CPF/pasta <br> - ZIP com assinaturas organizadas por CPF/pasta <br> - Excel separado para pendentes e concluídos <br> - Downloads assíncronos com notificação |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G011 |
| **Título** | Acessar Histórico Completo de Ações |
| **Descrição** | Como **Gerente** <br> Quero **visualizar logs de todas as ações do sistema** <br> Para que **eu possa fazer auditoria e rastreamento** |
| **Contexto / Observações** | - Logs de início/fim de coletas <br> - Logs de cadastros e alterações <br> - Filtros por tipo de ação, empresa, período |
| **Cenários** | 1. **VISUALIZAR LOGS GERAIS** <br> Dado que acesso aba "Histórico" <br> Quando a página carregar <br> Então devo ver lista completa de ações do sistema <br><br> 2. **FILTRAR POR TIPO DE AÇÃO** <br> Dado que seleciono "Início de Coleta" <br> Quando aplicar filtro <br> Então deve mostrar apenas ações de início de coleta <br><br> 3. **EXPORTAR HISTÓRICO** <br> Dado que preciso de relatório de auditoria <br> Quando clicar em "Exportar" <br> Então deve gerar arquivo com logs filtrados |
| **Critérios de Aceitação** | - Logs com timestamp, usuário, ação, IP <br> - Tipos de ação: início coleta, fim coleta, cadastros, alterações <br> - Filtros por empresa, período, tipo <br> - Exportação em CSV/Excel <br> - Performance otimizada |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-G012 |
| **Título** | Ativar/Desativar Empresa |
| **Descrição** | Como **Gerente** <br> Quero **ativar ou desativar empresas** <br> Para que **eu possa controlar acesso ao sistema** |
| **Contexto / Observações** | - Empresa desativada não pode iniciar coletas <br> - Profissionais de empresa desativada não conseguem logar <br> - Histórico deve ser mantido |
| **Cenários** | 1. **DESATIVAR EMPRESA** <br> Dado que seleciono uma empresa ativa <br> Quando clicar em "Desativar" <br> Então empresa deve ter status alterado e acessos bloqueados <br><br> 2. **REATIVAR EMPRESA** <br> Dado que seleciono empresa inativa <br> Quando clicar em "Ativar" <br> Então empresa deve voltar a ter acesso normal <br><br> 3. **TENTAR ACESSAR EMPRESA DESATIVADA** <br> Dado que empresa está inativa <br> Quando profissional tentar logar <br> Então deve exibir "Acesso temporariamente indisponível" |
| **Critérios de Aceitação** | - Alteração de status deve ser imediata <br> - Bloqueio de acesso efetivo <br> - Histórico e dados mantidos <br> - Log da ação registrado |
