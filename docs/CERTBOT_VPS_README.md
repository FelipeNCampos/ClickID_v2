# Obtain Let's Encrypt certificates (VPS) — webroot method

This snippet guides you through obtaining Let's Encrypt certificates for the project using the webroot plugin (the `deploy/nginx/webroot` directory is mounted by nginx and by the `certbot` service).

Prerequisites
- DNS A record(s) for your domain(s) pointing to the VPS public IP.
- Port 80 reachable from the Internet (ACME http-01 challenge).
- `docker` and `docker compose` available on the VPS.
- Make sure `deploy/nginx/default.conf` `server_name` is set to your domain (replace `credenciais.com.br`).

Update environment
1. Create or update `.env` in the project root with the following values (example):

LETSENCRYPT_DOMAINS=example.com,www.example.com
LETSENCRYPT_EMAIL=admin@example.com

Note: use comma-separated domains with no spaces.

Start web + nginx
Start the services that must serve the challenge (at minimum `web` and `nginx`).

# Bash (Linux VPS)
docker compose up -d web nginx

# PowerShell (if on Windows host)
docker compose up -d web nginx

Request certificates (production)
Run the certbot service in one-shot mode (this uses the `command` already set in `docker-compose.yml`).

# Bash (recommended on VPS)
docker compose run --rm certbot

# To test against Let's Encrypt staging (avoid rate limits):
# Run manually if you want to append the staging flag
docker compose run --rm --entrypoint "sh -c" certbot \"certbot certonly --webroot -w /var/www/certbot -d ${LETSENCRYPT_DOMAINS} --email ${LETSENCRYPT_EMAIL} --agree-tos --no-eff-email --staging --non-interactive\"

If certbot runs successfully you should see files under the `certs` volume (mounted into the `nginx` container at `/etc/letsencrypt`).

Quick verification
- Check the challenge path is reachable from Internet before running certbot:

# Example (replace example.com)
# Bash
echo "test" > deploy/nginx/webroot/testfile
curl -v http://example.com/.well-known/acme-challenge/testfile

If you get the `test` response, the webroot is correctly served by nginx.

Enable TLS in nginx
Once certificates are obtained, enable the TLS server block in `deploy/nginx/default.conf` (remove the commented TLS server block) and reload nginx.

# Reload nginx (after enabling TLS block)
docker compose exec nginx nginx -s reload

Renewal (recommended)
You should schedule automatic renewals. Example using host's cron (runs twice daily):

# Edit root crontab (or a dedicated user crontab)
# Example entry: run daily at 2:30 and 14:30
30 2,14 * * * cd /path/to/ClickID_v2 && docker compose run --rm certbot renew --deploy-hook "docker compose exec nginx nginx -s reload" >> /var/log/certbot-renew.log 2>&1

If you prefer systemd timers or a containerized cron, adapt accordingly.

Troubleshooting
- "Certbot doesn't know how to automatically configure the web server": that's expected if certbot can't modify nginx. We use `certonly --webroot` which avoids automatic nginx config.
- HTTP challenge fails: ensure nginx is running and `/.well-known/acme-challenge/` is served from `deploy/nginx/webroot` and port 80 is open.
- Rate limit: use `--staging` flag for testing.
- `ERROR: for <service> 'ContainerConfig'`: this usually happens when the VPS is still using legacy Compose v1 (`docker-compose` 1.29.x). Prefer `docker compose ...` with the Compose plugin (`docker-compose-plugin`). If the old `web` container is stuck from a previous run, remove it with `docker rm -f clickid_v2_web_1` and retry with `docker compose up -d --build`.

Notes and extras
- The `docker-compose.yml` includes a `certbot` service that uses the webroot plugin and reads `LETSENCRYPT_DOMAINS` and `LETSENCRYPT_EMAIL` from `.env`—running `docker compose run --rm certbot` will invoke that command.
- For an automated full flow, you can script `docker compose run --rm certbot` and follow with `docker compose exec nginx nginx -s reload`.

If you want, I can prepare a short `systemd` timer unit or a small host `cron` setup file to install on the VPS for automatic renewal and reloading. Would you like that next?
