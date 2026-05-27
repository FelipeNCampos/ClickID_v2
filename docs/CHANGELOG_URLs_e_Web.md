# API REST
http://127.0.0.1:8000/api/v1/usuarios/
http://127.0.0.1:8000/api/v1/empresas/
http://127.0.0.1:8000/api/v1/profissionais/
http://127.0.0.1:8000/api/v1/modelos/
http://127.0.0.1:8000/api/v1/campos/
http://127.0.0.1:8000/api/v1/coletas/
http://127.0.0.1:8000/api/v1/dashboards/
{BASE_URL}/api/v1/usuarios/
{BASE_URL}/api/v1/empresas/
{BASE_URL}/api/v1/profissionais/
{BASE_URL}/api/v1/modelos/
{BASE_URL}/api/v1/campos/
{BASE_URL}/api/v1/coletas/
{BASE_URL}/api/v1/dashboards/
# Site Web
http://127.0.0.1:8000/gerente/login/
http://127.0.0.1:8000/gerente/dashboard/
http://127.0.0.1:8000/empresa/dashboard/
http://127.0.0.1:8000/coleta/<token>/
{BASE_URL}/gerente/login/
{BASE_URL}/gerente/dashboard/
{BASE_URL}/empresa/dashboard/
{BASE_URL}/coleta/<token>/
# Admin
http://127.0.0.1:8000/admin/
{BASE_URL}/admin/
# 2. Servidor Web
```bash
python manage.py runserver
# ✅ Starting development server at {BASE_URL} (e.g. http://127.0.0.1:8000 for local dev)
# ✅ Quit the server with CTRL-BREAK.
```
# 2. Acessar Login
```
{BASE_URL}/gerente/login/
```
# Login via API
curl -X POST {BASE_URL}/api/v1/auth/login/ \
# Usar token para acessar recursos
curl {BASE_URL}/api/v1/empresas/ \
# 2. Iniciar Servidor
```bash
## Correções e Melhorias Implementadas - ClickID v2

### 🔧 Problema Corrigido: Repetição de `api/v1` nas URLs

#### Problema Identificado
As URLs da API estavam sendo registradas com repetição do prefixo `api/v1/`, causando erro 404 em chamadas REST (ex.: `{BASE_URL}/api/v1/api/v1/usuarios/`).

#### Solução Implementada
Refatoração de `clickid_core/urls.py` para agrupar os includes da API sob um único `path('api/v1/', ...)` e evitar duplicações.

#### URLs Resultantes (Exemplos)
```
{BASE_URL}/api/v1/usuarios/
{BASE_URL}/api/v1/empresas/
{BASE_URL}/api/v1/profissionais/
{BASE_URL}/api/v1/modelos/
{BASE_URL}/api/v1/campos/
{BASE_URL}/api/v1/coletas/
{BASE_URL}/api/v1/dashboards/

{BASE_URL}/gerente/login/
{BASE_URL}/gerente/dashboard/
{BASE_URL}/empresa/dashboard/
{BASE_URL}/coleta/<token>/

{BASE_URL}/admin/
```

> Nota: `{BASE_URL}` é um placeholder usado neste documento. Para desenvolvimento local, isso normalmente é `http://127.0.0.1:8000`.

---

## 🌐 Nova Funcionalidade: Interface Web Completa

O sistema agora fornece uma interface web que consome a API REST e inclui páginas para gerentes, empresas e profissionais.

### Exemplos de uso (com placeholders)
```python
# Login via API
response = requests.post(
    '{BASE_URL}/api/v1/auth/login/',
    json={'email': email, 'password': password}
)

# Usar token para acessar recursos
curl {BASE_URL}/api/v1/empresas/ -H "Authorization: Bearer <token>"
```

---

## 🚀 Como Testar (local)

```bash
# Iniciar servidor (local)
python manage.py runserver

# Acessar (exemplo)
{BASE_URL}/gerente/login/
```

---

## Observações
- Este arquivo teve URLs locais substituídas por `{BASE_URL}` para tornar a documentação portátil entre ambientes.
- Não altere variáveis de configuração de desenvolvimento (`.env`) com placeholders; mantenha `http://localhost:3000` em `.env` para exemplos locais quando apropriado.
