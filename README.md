# ClickID v2 - Sistema de Coleta de Dados Multimídia

## 📋 Sobre o Projeto

Sistema web e API para coleta de dados multimídia destinado à confecção de carteiras profissionais digitais. Implementa arquitetura multi-tenant com três tipos de usuários (Gerente, Empresa e Profissional).

## 🏗️ Arquitetura

- **Backend**: Django 5.2 + Django REST Framework
- **Banco de Dados**: PostgreSQL (SQLite para desenvolvimento)
- **Cache**: Redis
- **Filas**: Celery + RabbitMQ
- **Storage**: Amazon S3
- **Autenticação**: JWT (Simple JWT)

## 📁 Estrutura do Projeto

```
ClickID_v2/
├── clickid_core/          # Configurações principais do projeto
├── usuarios/              # App de usuários (Gerente, Usuario base, LogAuditoria)
├── empresas/              # App de empresas (Empresa, Profissional, Departamento)
├── coletas/               # App de coletas (Coleta, ColetaProfissional, Respostas)
├── modelos/               # App de modelos (ModeloCartao, CampoCartao)
├── dashboard/             # App de dashboard e métricas
├── docs/                  # Documentação completa
│   ├── HU/               # Histórias de usuário
│   └── UML/              # Diagramas UML
├── media/                 # Arquivos de mídia (desenvolvimento)
├── static/                # Arquivos estáticos
└── requirements.txt       # Dependências Python
```

## 🚀 Setup Inicial

### 1. Ambiente Virtual

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente

Crie um arquivo `.env` na raiz:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=clickid_db
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Redis & Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://127.0.0.1:6379/1

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_app

# AWS S3
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=clickid-media
AWS_S3_REGION_NAME=us-east-1

# CORS
# Use a placeholder for the frontend origin in docs. Set this to your frontend origin in production, e.g. `http://example.com` or `http://localhost:3000` for development.
CORS_ALLOWED_ORIGINS={FRONTEND_ORIGIN}  # e.g. http://localhost:3000
```

### 4. Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Criar Superusuário

```bash
python manage.py createsuperuser
```

### 6. Rodar Servidor

```bash
python manage.py runserver
```

## 📚 Documentação

### Histórias de Usuário

- **HU_Gerente.md**: 12 histórias de usuário do Gerente
- **HU_Empresa.md**: 10 histórias de usuário da Empresa  
- **HU_Profissional.md**: 13 histórias de usuário do Profissional

### Diagramas UML

- **diagrama_classes.puml**: Diagrama de classes completo
- **diagrama_casos_uso.puml**: 38 casos de uso
- **diagrama_sequencia_coleta.puml**: Fluxo completo de coleta
- **diagrama_sequencia_modelo_canvas.puml**: Criação de modelos canvas
- **diagrama_estados_coleta.puml**: Máquina de estados da coleta
- **diagrama_estados_profissional_coleta.puml**: Estados do preenchimento
- **diagrama_atividades_dashboard.puml**: Fluxo do dashboard
- **diagrama_componentes.puml**: Arquitetura em camadas
- **diagrama_implantacao.puml**: Infraestrutura e deployment

## 🔑 Funcionalidades Principais

### Gerente
- Cadastrar empresas e outros gerentes
- Criar modelos de cartões com canvas drag-and-drop
- Iniciar coletas para empresas (segmentadas ou completas)
- Dashboard analítica com métricas
- Logs de auditoria completos
- Exportação de dados e mídias

### Empresa
- Cadastrar profissionais (individual ou via Excel)
- Organizar profissionais em departamentos
- Iniciar coletas segmentadas
- Gerenciar modelos de cartões privados
- Baixar relatórios e mídias
- Dashboard com métricas da empresa

### Profissional
- Login com CPF + senha padrão (4 últimos dígitos)
- Alteração obrigatória de senha no primeiro acesso
- Preencher formulários dinâmicos
- Capturar foto via câmera ou upload
- Assinar digitalmente em canvas
- Visualizar histórico de formulários

## 🎨 Modelos de Cartões Canvas

Os modelos são **privados por empresa** e criados com editor canvas:

- Dimensões reais do cartão (ex: 85mm x 54mm)
- Campos arrastáveis e posicionáveis
- Configurações visuais: fonte, cor, tamanho, alinhamento
- Configurações de formulário: pergunta, validação, obrigatoriedade
- Preview em tempo real
- Geração automática de formulários baseada nos campos

## 🔐 Autenticação

### JWT Token

```bash
POST /api/auth/login/
{
  "email": "usuario@example.com",
  "password": "senha123"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "usuario@example.com",
    "tipo_usuario": "gerente"
  }
}
```

### Headers

```
Authorization: Bearer <access_token>
```

## 📊 Multi-Tenancy

O sistema implementa isolamento completo de dados:

- Cada empresa tem seus próprios modelos de cartões
- Profissionais vinculados apenas à sua empresa
- Coletas isoladas por empresa
- URLs personalizadas por empresa

## ⚙️ Tasks Assíncronas (Celery)

```bash
# Worker
celery -A clickid_core worker -l info

# Beat (agendador)
celery -A clickid_core beat -l info
```

### Tasks Implementadas

- Envio de emails em lote
- Processamento de importação Excel
- Geração de relatórios
- Otimização de imagens
- Geração de cartões finais

## 🧪 Testes

```bash
python manage.py test
```

## 📦 Models Criados

### usuarios/models.py
- ✅ Usuario (AbstractBaseUser)
- ✅ Gerente
- ✅ LogAuditoria

### empresas/models.py
- ✅ Empresa
- ✅ Departamento
- ✅ Profissional

### modelos/models.py (A criar)
- ModeloCartao
- CampoCartao
- TipoCampo (Enum)

### coletas/models.py (A criar)
- Coleta
- ColetaProfissional
- RespostaColeta
- RespostaCampo
- Foto
- Assinatura
- Notificacao
- LogEmail

## 🎯 Próximos Passos

1. ✅ Criar estrutura base do projeto Django
2. ✅ Configurar settings com todas as integrações
3. ✅ Implementar models de usuários e empresas
4. ⏳ Implementar models de modelos/cartões
5. ⏳ Implementar models de coletas
6. ⏳ Criar serializers para API REST
7. ⏳ Implementar ViewSets e endpoints
8. ⏳ Criar services (Excel, Email, Canvas)
9. ⏳ Implementar Celery tasks
10. ⏳ Criar templates frontend

## 📝 Comandos Úteis

```bash
# Criar nova migration
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Shell interativo
python manage.py shell

# Coletar arquivos estáticos
python manage.py collectstatic

# Rodar servidor
python manage.py runserver 0.0.0.0:8000
```

## 🐛 Debug

```python
# No shell Django
python manage.py shell

from usuarios.models import Usuario
from empresas.models import Empresa, Profissional

# Criar usuário gerente
usuario = Usuario.objects.create_user(
    email='gerente@clickid.com',
    password='senha123'
)
gerente = Gerente.objects.create(
    usuario=usuario,
    nome='João Silva',
    cpf='12345678901',
    telefone='11999999999'
)
```

### Debug helper: permitir botão de inspeção por IP

Para facilitar depuração sem ativar `DEBUG=True` em produção, o projeto suporta uma variável de ambiente `DEBUG_ALLOWED_IPS`.

- `DEBUG_ALLOWED_IPS`: lista separada por vírgulas de endereços IP que devem ver o botão de debug no UI (ex.: `127.0.0.1,192.168.1.100`).

Exemplo `.env`:

```env
DEBUG_ALLOWED_IPS=127.0.0.1,192.168.1.100
```

Como funciona:
- A view de preenchimento injeta `debug=True` no contexto se `settings.DEBUG` for verdadeiro ou se o `REMOTE_ADDR` da requisição fizer parte de `DEBUG_ALLOWED_IPS`.
- Isso mostra o botão **Mostrar debug dos campos** na página de preenchimento, permitindo inspecionar o JSON que o backend injeta (`#campos-data`).

Após alterar `.env`, reinicie o serviço `web` para aplicar a mudança:

```powershell
docker compose restart web
docker compose logs --tail 200 web
```


## 📄 Licença

Projeto privado - Todos os direitos reservados

## 👥 Equipe

- Desenvolvimento: ClickID Team
- Documentação: Baseada em UML e Histórias de Usuário

---

**Status**: 🚧 Em Desenvolvimento - Fase Inicial
