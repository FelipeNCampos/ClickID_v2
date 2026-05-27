#!/bin/sh
# Helper script to request Let's Encrypt certificates using the docker-compose certbot service.
# Usage:
# 1. Fill .env with LETSENCRYPT_DOMAINS and LETSENCRYPT_EMAIL
# 2. Ensure nginx is running and serving /.well-known/acme-challenge from ./deploy/nginx/webroot
# 3. Run: docker compose run --rm certbot

if [ -z "$LETSENCRYPT_DOMAINS" ] || [ -z "$LETSENCRYPT_EMAIL" ]; then
  echo "Please set LETSENCRYPT_DOMAINS and LETSENCRYPT_EMAIL in .env before running."
  exit 1
fi

echo "Requesting certs for: $LETSENCRYPT_DOMAINS"
docker compose run --rm certbot

echo "If certs were obtained, enable the TLS server block in 'deploy/nginx/default.conf' and reload nginx."
