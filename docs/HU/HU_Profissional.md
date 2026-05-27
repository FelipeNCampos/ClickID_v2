# Histórias de Usuário - PROFISSIONAL

## 👨‍💼 Sistema de Coleta de Dados Multimídia - ClickID

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P001 |
| **Título** | Acessar Portal via Link da Empresa |
| **Descrição** | Como **Profissional** <br> Quero **acessar página de login da minha empresa** <br> Para que **eu possa preencher meus dados** |
| **Contexto / Observações** | - Acesso via URL personalizada da empresa <br> - Link enviado por email <br> - Interface com branding da empresa |
| **Cenários** | 1. **ACESSAR VIA LINK** <br> Dado que recebo email com link da empresa <br> Quando clicar no link <br> Então devo ser direcionado para página de login personalizada <br><br> 2. **LINK INVÁLIDO** <br> Dado que acesso link de empresa inexistente <br> Quando tentar acessar <br> Então deve exibir "Empresa não encontrada" <br><br> 3. **EMPRESA DESATIVADA** <br> Dado que empresa foi desativada <br> Quando tentar acessar <br> Então deve exibir "Acesso temporariamente indisponível" |
| **Critérios de Aceitação** | - URL personalizada funcional <br> - Branding da empresa visível (logo, cores) <br> - Redirecionamento correto <br> - Mensagens de erro claras |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P002 |
| **Título** | Realizar Primeiro Login |
| **Descrição** | Como **Profissional** <br> Quero **fazer meu primeiro login com CPF e senha padrão** <br> Para que **eu possa acessar o sistema** |
| **Contexto / Observações** | - Login: CPF (apenas números) <br> - Senha padrão: 4 últimos dígitos do CPF <br> - Obrigatório alterar senha após primeiro login |
| **Cenários** | 1. **PRIMEIRO LOGIN VÁLIDO** <br> Dado que insiro meu CPF e 4 últimos dígitos <br> Quando clicar em "Entrar" <br> Então devo ser forçado a criar nova senha <br><br> 2. **CPF NÃO CADASTRADO** <br> Dado que insiro CPF não vinculado à empresa <br> Quando tentar logar <br> Então deve exibir "CPF não encontrado. Entre em contato com sua empresa" <br><br> 3. **SENHA PADRÃO INCORRETA** <br> Dado que insiro senha diferente dos 4 últimos dígitos <br> Quando tentar logar pela primeira vez <br> Então deve exibir "Senha incorreta. Use os 4 últimos dígitos do CPF" |
| **Critérios de Aceitação** | - Validação de CPF (apenas números) <br> - Senha padrão: últimos 4 dígitos <br> - Forçar alteração de senha no primeiro acesso <br> - Mensagens de erro claras <br> - Log de primeiro acesso |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P003 |
| **Título** | Alterar Senha no Primeiro Acesso |
| **Descrição** | Como **Profissional** <br> Quero **criar minha própria senha** <br> Para que **eu possa ter acesso seguro ao sistema** |
| **Contexto / Observações** | - Obrigatório após primeiro login <br> - Senha deve atender critérios de segurança <br> - Confirmação de senha necessária |
| **Cenários** | 1. **CRIAR SENHA VÁLIDA** <br> Dado que estou na tela de alteração obrigatória <br> Quando inserir nova senha que atende critérios <br> Então senha deve ser salva e devo acessar sistema <br><br> 2. **SENHA FRACA** <br> Dado que insiro senha com menos de 8 caracteres <br> Quando tentar salvar <br> Então deve exibir "Senha deve ter no mínimo 8 caracteres" <br><br> 3. **SENHAS NÃO CONFEREM** <br> Dado que confirmação difere da senha <br> Quando tentar salvar <br> Então deve exibir "Senhas não conferem" |
| **Critérios de Aceitação** | - Mínimo 8 caracteres <br> - Ao menos 1 letra maiúscula <br> - Ao menos 1 número <br> - Confirmação obrigatória <br> - Não permitir pular esta etapa |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P004 |
| **Título** | Visualizar Formulários Pendentes |
| **Descrição** | Como **Profissional** <br> Quero **ver lista de formulários que preciso preencher** <br> Para que **eu saiba quais coletas estão aguardando** |
| **Contexto / Observações** | - Listagem após login <br> - Apenas formulários não finalizados <br> - Indicação do tipo de coleta (dados, foto, assinatura) |
| **Cenários** | 1. **VISUALIZAR PENDÊNCIAS** <br> Dado que faço login <br> Quando acessar página inicial <br> Então devo ver lista de formulários pendentes <br><br> 2. **NENHUMA PENDÊNCIA** <br> Dado que já finalizei todos os formulários <br> Quando acessar sistema <br> Então deve exibir "Você não possui formulários pendentes" <br><br> 3. **ACESSAR FORMULÁRIO** <br> Dado que clico em formulário pendente <br> Quando clicar <br> Então devo ser direcionado para tela de preenchimento |
| **Critérios de Aceitação** | - Lista clara com nome da coleta e tipo <br> - Indicação visual: dados, foto, assinatura <br> - Botão "Preencher" visível <br> - Mensagem quando não houver pendências <br> - Interface responsiva para mobile |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P005 |
| **Título** | Preencher Formulário de Dados |
| **Descrição** | Como **Profissional** <br> Quero **preencher campos de texto do formulário** <br> Para que **meus dados sejam coletados** |
| **Contexto / Observações** | - Formulário baseado em modelo da gerência <br> - Campos obrigatórios e opcionais <br> - Validações em tempo real |
| **Cenários** | 1. **PREENCHER DADOS VÁLIDOS** <br> Dado que preencho todos os campos obrigatórios <br> Quando clicar em "Salvar" <br> Então dados devem ser persistidos <br><br> 2. **CAMPOS OBRIGATÓRIOS VAZIOS** <br> Dado que deixo campo obrigatório em branco <br> Quando tentar avançar <br> Então campo deve ser destacado com erro <br><br> 3. **SALVAR RASCUNHO** <br> Dado que preencho parcialmente <br> Quando clicar em "Salvar Rascunho" <br> Então devo poder continuar depois |
| **Critérios de Aceitação** | - Validação client-side e server-side <br> - Campos obrigatórios destacados com * <br> - Salvamento automático de rascunho a cada 2 minutos <br> - Mensagens de erro específicas <br> - Interface responsiva |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P006 |
| **Título** | Capturar Foto Profissional |
| **Descrição** | Como **Profissional** <br> Quero **tirar minha foto diretamente no navegador** <br> Para que **ela seja incluída na minha carteira** |
| **Contexto / Observações** | - Acesso à câmera do dispositivo <br> - Preview antes de confirmar <br> - Possibilidade de refazer |
| **Cenários** | 1. **TIRAR FOTO COM CÂMERA** <br> Dado que permito acesso à câmera <br> Quando tirar foto <br> Então devo ver preview e poder confirmar ou refazer <br><br> 2. **CÂMERA NEGADA** <br> Dado que nego permissão de câmera <br> Quando tentar capturar <br> Então deve permitir upload de arquivo <br><br> 3. **REFAZER FOTO** <br> Dado que não gostei da foto <br> Quando clicar em "Tirar Novamente" <br> Então devo poder capturar nova foto |
| **Critérios de Aceitação** | - Resolução mínima: 300x400 pixels <br> - Formatos: JPG, PNG <br> - Tamanho máximo: 5MB <br> - Preview em tela cheia <br> - Funcional em mobile e desktop |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P007 |
| **Título** | Fazer Upload de Foto |
| **Descrição** | Como **Profissional** <br> Quero **fazer upload de foto do dispositivo** <br> Para que **eu possa enviar foto já existente** |
| **Contexto / Observações** | - Alternativa à captura por câmera <br> - Validação de formato e tamanho <br> - Preview antes de confirmar |
| **Cenários** | 1. **UPLOAD VÁLIDO** <br> Dado que seleciono foto JPG do celular <br> Quando fazer upload <br> Então foto deve ser carregada com preview <br><br> 2. **FORMATO INVÁLIDO** <br> Dado que seleciono arquivo PDF <br> Quando tentar enviar <br> Então deve exibir "Formato inválido. Use JPG ou PNG" <br><br> 3. **ARQUIVO MUITO GRANDE** <br> Dado que seleciono foto de 10MB <br> Quando tentar enviar <br> Então deve exibir "Arquivo muito grande. Máximo 5MB" |
| **Critérios de Aceitação** | - Formatos aceitos: JPG, PNG <br> - Tamanho máximo: 5MB <br> - Preview após upload <br> - Possibilidade de substituir <br> - Mensagens de erro claras |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P008 |
| **Título** | Assinar Digitalmente |
| **Descrição** | Como **Profissional** <br> Quero **desenhar minha assinatura na tela** <br> Para que **ela seja incluída na minha carteira** |
| **Contexto / Observações** | - Canvas HTML5 para desenho <br> - Suporte a mouse e touch <br> - Possibilidade de limpar e refazer |
| **Cenários** | 1. **ASSINAR CORRETAMENTE** <br> Dado que desenho minha assinatura no canvas <br> Quando clicar em "Confirmar" <br> Então assinatura deve ser salva como imagem <br><br> 2. **ASSINATURA MUITO SIMPLES** <br> Dado que faço apenas um traço rápido <br> Quando tentar confirmar <br> Então deve exibir "Assinatura muito simples. Por favor, assine novamente" <br><br> 3. **LIMPAR ASSINATURA** <br> Dado que não gostei da assinatura <br> Quando clicar em "Limpar" <br> Então canvas deve ser resetado |
| **Critérios de Aceitação** | - Canvas responsivo (mobile e desktop) <br> - Suporte a mouse e touch <br> - Validação de complexidade mínima <br> - Formato PNG com fundo transparente <br> - Preview após confirmar |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P009 |
| **Título** | Finalizar Formulário |
| **Descrição** | Como **Profissional** <br> Quero **concluir e enviar formulário completo** <br> Para que **meus dados sejam processados** |
| **Contexto / Observações** | - Validação completa antes de envio <br> - Confirmação visual de conclusão <br> - Impossibilidade de editar após finalizar |
| **Cenários** | 1. **FINALIZAR COM SUCESSO** <br> Dado que preenchi todos os campos obrigatórios <br> Quando clicar em "Finalizar" <br> Então deve exibir confirmação e marcar como concluído <br><br> 2. **CAMPOS PENDENTES** <br> Dado que deixei campos obrigatórios vazios <br> Quando tentar finalizar <br> Então deve destacar campos pendentes <br><br> 3. **CONFIRMAÇÃO DE ENVIO** <br> Dado que finalizei formulário <br> Quando enviar <br> Então devo receber email de confirmação |
| **Critérios de Aceitação** | - Validação completa de todos os campos <br> - Mensagem de sucesso clara <br> - Email de confirmação enviado <br> - Formulário marcado como "Concluído" <br> - Redirecionamento para página de sucesso |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P010 |
| **Título** | Visualizar Histórico de Formulários |
| **Descrição** | Como **Profissional** <br> Quero **ver lista de formulários já preenchidos** <br> Para que **eu possa confirmar quais já finalizei** |
| **Contexto / Observações** | - Listagem de formulários concluídos <br> - Data de conclusão visível <br> - Sem possibilidade de edição |
| **Cenários** | 1. **VISUALIZAR CONCLUÍDOS** <br> Dado que acesso aba "Histórico" <br> Quando a página carregar <br> Então devo ver lista de formulários finalizados <br><br> 2. **VER DETALHES** <br> Dado que clico em formulário concluído <br> Quando acessar <br> Então devo ver resumo do que foi enviado (sem edição) <br><br> 3. **NENHUM HISTÓRICO** <br> Dado que nunca finalizei formulário <br> Quando acessar histórico <br> Então deve exibir "Você ainda não finalizou nenhum formulário" |
| **Critérios de Aceitação** | - Lista ordenada por data de conclusão <br> - Indicação visual de status "Concluído" <br> - Visualização em modo leitura <br> - Data e hora da conclusão visíveis |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P011 |
| **Título** | Recuperar Senha |
| **Descrição** | Como **Profissional** <br> Quero **recuperar minha senha caso esqueça** <br> Para que **eu possa voltar a acessar o sistema** |
| **Contexto / Observações** | - Link "Esqueci minha senha" na tela de login <br> - Envio de email com token de recuperação <br> - Token com validade de 24h |
| **Cenários** | 1. **SOLICITAR RECUPERAÇÃO** <br> Dado que clico em "Esqueci minha senha" <br> Quando informar meu CPF <br> Então devo receber email com link de redefinição <br><br> 2. **CPF NÃO CADASTRADO** <br> Dado que insiro CPF não vinculado <br> Quando solicitar recuperação <br> Então deve exibir "CPF não encontrado" <br><br> 3. **REDEFINIR SENHA** <br> Dado que acesso link do email <br> Quando criar nova senha <br> Então devo poder fazer login com nova senha |
| **Critérios de Aceitação** | - Email enviado com link seguro <br> - Token expira em 24h <br> - Nova senha deve atender critérios de segurança <br> - Confirmação de alteração <br> - Log de recuperação registrado |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P012 |
| **Título** | Receber Notificações por Email |
| **Descrição** | Como **Profissional** <br> Quero **receber emails sobre minhas pendências** <br> Para que **eu não perca prazos importantes** |
| **Contexto / Observações** | - Notificação ao ser cadastrado em coleta <br> - Lembretes para formulários pendentes <br> - Confirmação de conclusão |
| **Cenários** | 1. **COLETA INICIADA** <br> Dado que fui incluído em uma coleta <br> Quando coleta for criada <br> Então devo receber email com link de acesso <br><br> 2. **LEMBRETE DE PENDÊNCIA** <br> Dado que não finalizei formulário em 7 dias <br> Quando atingir prazo <br> Então devo receber email de lembrete <br><br> 3. **CONFIRMAÇÃO DE CONCLUSÃO** <br> Dado que finalizei formulário <br> Quando enviar <br> Então devo receber email de confirmação |
| **Critérios de Aceitação** | - Templates profissionais de email <br> - Links diretos para formulários <br> - Frequência de lembretes configurável <br> - Unsubscribe funcional <br> - Logs de envio registrados |

---

| Seção | Conteúdo |
|-----------------------|---------------------------------------------------------------------------|
| **ID da História** | US-P013 |
| **Título** | Visualizar Progresso do Formulário |
| **Descrição** | Como **Profissional** <br> Quero **ver quanto falta para concluir** <br> Para que **eu saiba meu progresso** |
| **Contexto / Observações** | - Barra de progresso visual <br> - Indicação de etapas concluídas <br> - Atualização em tempo real |
| **Cenários** | 1. **VISUALIZAR PROGRESSO** <br> Dado que estou preenchendo formulário <br> Quando preencher campos <br> Então barra de progresso deve atualizar automaticamente <br><br> 2. **ETAPAS MÚLTIPLAS** <br> Dado que formulário tem dados, foto e assinatura <br> Quando finalizar cada etapa <br> Então deve marcar como concluída visualmente <br><br> 3. **PROGRESSO SALVO** <br> Dado que saio do formulário <br> Quando voltar depois <br> Então progresso deve ser mantido |
| **Critérios de Aceitação** | - Barra de progresso percentual <br> - Indicação visual de etapas (dados, foto, assinatura) <br> - Atualização em tempo real <br> - Salvamento automático de progresso <br> - Design claro e intuitivo |
