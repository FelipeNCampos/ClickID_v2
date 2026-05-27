# Deploy Docker em Ubuntu (guia rápido)

Este passo a passo mostra como subir a aplicação ClickID usando Docker Compose em uma máquina Ubuntu.

Pré-requisitos:
- Uma máquina Ubuntu 20.04+ com acesso root/sudo
 Nome de domínio configurado apontando para a máquina (ex: `credenciais.com.br`)
 DJANGO_ALLOWED_HOSTS=credenciais.com.br,localhost
 DJANGO_SUPERUSER_USERNAME=admin
 DJANGO_SUPERUSER_EMAIL=felipe@gmail.com
 DJANGO_SUPERUSER_PASSWORD=flexa8000
 Usamos o serviço `certbot` em `docker-compose.prod.yml`. Para conseguir um certificado para `credenciais.com.br`, execute o comando abaixo:
 docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d credenciais.com.br --email seu@email -n --agree-tos
 Observação: o `default.conf` foi configurado para usar `/etc/letsencrypt/live/credenciais.com.br/...`. Se você usar outro domínio, atualize `deploy/nginx/default.conf` adequadamente ou crie links simbólicos no volume `certs`.
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update; sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
```

2) Preparar repositório e variáveis

Clone o repositório e crie um arquivo `.env.prod` (não commitar credenciais) com as variáveis mínimas:

```
POSTGRES_DB=clickid
POSTGRES_USER=clickid
POSTGRES_PASSWORD=um_senha_segura
DATABASE_URL=postgres://clickid:um_senha_segura@db:5432/clickid
DJANGO_SECRET_KEY=uma_chave_secreta_aqui
DJANGO_ALLOWED_HOSTS=example.com,localhost
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin1234
```

3) Gerar certificados (opcional)

Usamos o serviço `certbot` em `docker-compose.prod.yml`. Para conseguir um certificado, execute um comando semelhante (substitua `example.com`):

```bash
# Parar nginx temporariamente se já ouvindo na porta 80
docker compose -f docker-compose.prod.yml up -d --build

# Em outra shell: criar certificado para domain
docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d example.com --email seu@email -n --agree-tos

# Após cert gerar, reiniciar nginx para carregar certs
docker compose -f docker-compose.prod.yml restart nginx
```

Observação: o `default.conf` referencia `/etc/letsencrypt/live/yourdomain/...`. Atualize `yourdomain` para seu domínio ou use variáveis/links simbólicos.

4) Subir o ambiente (produção)

```bash
# Build e start em background
docker compose -f docker-compose.prod.yml up -d --build

# Ver logs
docker compose -f docker-compose.prod.yml logs -f web

# Verificar containers
docker ps
```

5) Systemd (opcional): rodar compose no boot

Crie `/etc/systemd/system/clickid.service` com conteúdo:

```
[Unit]
Description=ClickID Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/clickid  # ajustar para o caminho do projeto
ExecStart=/usr/bin/docker compose -f /opt/clickid/docker-compose.prod.yml up -d --build
ExecStop=/usr/bin/docker compose -f /opt/clickid/docker-compose.prod.yml down

[Install]
WantedBy=multi-user.target
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now clickid.service
```

6) Troubleshooting rápido
- Logs: `docker compose -f docker-compose.prod.yml logs -f web` e `docker compose ps`
- Verifique variáveis `.env.prod` e `DJANGO_ALLOWED_HOSTS`
- Erros de migrations: `docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate`

7) Segurança e recomendações
- Use um arquivo `.env.prod` fora do repositório e com permissões restritas
- Use volumes persistentes para `pgdata`, `media` e `certs`
- Configure backup do banco e dos uploads
