#!/usr/bin/env bash
set -e

echo "Entrypoint: aguardando servicos dependentes..."

mkdir -p /app/logs
touch /app/logs/clickid.log

# Determine DB host variable (support DATABASE_HOST or DB_HOST)
DB_HOST=${DATABASE_HOST:-${DB_HOST:-}}
DB_PORT=${DATABASE_PORT:-${DB_PORT:-5432}}

if [ -n "$DB_HOST" ]; then
  echo "Aguardando banco $DB_HOST:$DB_PORT..."
  until nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
fi

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Coletando static files..."
python manage.py collectstatic --noinput || true

# Create a superuser if env provided. Use Django shell so it works with
# custom user models (email-based USERNAME_FIELD).
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Criando superuser (caso nao exista)..."
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if email and password:
    field = getattr(User, 'USERNAME_FIELD', 'username')
    if field == 'email':
        lookup = {'email': email}
    else:
        lookup = {field: username or email}

    if not User.objects.filter(**lookup).exists():
        if field == 'email':
            User.objects.create_superuser(email=email, password=password)
        else:
            User.objects.create_superuser(username or 'admin', email or '', password)
PY
fi

echo "Executando comando: $*"
exec "$@"
