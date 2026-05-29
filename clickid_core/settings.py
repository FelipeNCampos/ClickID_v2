"""
Django settings for clickid_core project - Sistema de Coleta de Dados Multimídia
"""

from pathlib import Path
from decouple import config
import socket
import warnings
from datetime import timedelta
from urllib.parse import urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def _csv_env(*names, default=''):
    for name in names:
        value = config(name, default=None)
        if value is not None:
            return [item.strip() for item in value.split(',') if item.strip()]
    return [item.strip() for item in default.split(',') if item.strip()]


def _normalize_origin(origin):
    parsed = urlparse(origin)
    if parsed.scheme and parsed.netloc:
        return origin

    host = origin.strip().lstrip('/')
    if not host:
        return host

    is_local = host.startswith('localhost') or host.startswith('127.0.0.1')
    scheme = 'http' if is_local else 'https'
    return f'{scheme}://{host}'


# Quick-start development settings
SECRET_KEY = config(
    'SECRET_KEY',
    default=config('DJANGO_SECRET_KEY', default='django-insecure-3shswymd)7v!!fa_=+39fpf^5ajf2hwdu0f^@v42-1mx_a55b@')
)
DEBUG = config('DEBUG', default=False, cast=bool)
# DEBUG_ALLOWED_IPS: comma separated list of IPs allowed to see debug UI (e.g. the debug button)
# This can be used in production for temporary debugging without enabling full DEBUG=True.
DEBUG_ALLOWED_IPS = config(
    'DEBUG_ALLOWED_IPS',
    default='127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
ALLOWED_HOSTS = _csv_env(
    'ALLOWED_HOSTS',
    'DJANGO_ALLOWED_HOSTS',
    default='localhost,127.0.0.1,177.201.85.3,credenciais.com.br'
)
for _default_host in ('localhost', '127.0.0.1'):
    if _default_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_default_host)

# Security: CSRF trusted origins and proxy settings
# Read a comma-separated list of origins (include scheme), e.g.:
# CSRF_TRUSTED_ORIGINS=https://credenciais.com.br,https://www.example.com
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://credenciais.com.br',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# If Django is behind a TLS-terminating proxy (nginx) that sets
# X-Forwarded-Proto, tell Django to respect that header so request.is_secure()
# returns True for proxied HTTPS requests.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Production cookie/security hardening (enable when DEBUG=False)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

# Permitir importação de arquivos grandes (1000+ registros)
# Default é 1000 campos - 50 registros x 20 campos = 1000
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Aumentar limite de upload para suportar fotos/assinaturas em base64
# Fotos podem facilmente ter 2-5 MB cada em base64
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB (padrão é 2.5 MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB (padrão é 2.5 MB)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Local apps
    'usuarios',
    'empresas',
    'coletas',
    'modelos',
    'dashboard',
    'auditoria',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'clickid_core.middleware.RequestLoggingMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clickid_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'clickid_core.context_processors.empresa_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'clickid_core.wsgi.application'


# Database
# Read DB settings from env (decouple)
_DB_ENGINE = config('DB_ENGINE', default='django.db.backends.postgresql')
_DB_NAME = config('DB_NAME', default='clickid_db')
_DB_USER = config('DB_USER', default='postgres')
_DB_PASSWORD = config('DB_PASSWORD', default='postgres')
_DB_HOST = config('DB_HOST', default='localhost')
_DB_PORT = config('DB_PORT', default='5432')

# If running locally (DEBUG=True) and the configured DB host cannot be resolved
# (for example DB_HOST='db' when Postgres runs inside Docker), fall back to
# a local sqlite database to keep development fast and avoid connection errors.
_use_sqlite_fallback = False
if DEBUG and _DB_ENGINE == 'django.db.backends.postgresql':
    try:
        # Try to resolve the DB host name to detect unreachable docker service
        socket.getaddrinfo(_DB_HOST, None)
    except Exception:
        warnings.warn(f"DB host '{_DB_HOST}' not resolvable — falling back to sqlite3 for local development.")
        _use_sqlite_fallback = True

if _use_sqlite_fallback:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': _DB_ENGINE,
            'NAME': _DB_NAME,
            'USER': _DB_USER,
            'PASSWORD': _DB_PASSWORD,
            'HOST': _DB_HOST,
            'PORT': _DB_PORT,
            'ATOMIC_REQUESTS': True,
            # Conexões persistentes: keep-alive in production is useful, but in
            # development heavy proxying (views calling local API) can exhaust
            # Postgres max_connections. When DEBUG=True force connections to
            # close at the end of each request to avoid 'too many clients'.
            'CONN_MAX_AGE': 0 if DEBUG else 60,
            'OPTIONS': {
                'connect_timeout': 10,
            } if _DB_ENGINE == 'django.db.backends.postgresql' else {},
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 4}},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom User Model
AUTH_USER_MODEL = 'usuarios.Usuario'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'clickid_core.pagination.LargeResultsSetPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}


# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [_normalize_origin(s.strip()) for s in v.split(',') if s.strip()]
)
CORS_ALLOW_CREDENTIALS = True


# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE


# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@clickid.com.br')


# AWS S3 Configuration
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='clickid-media')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'private'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

# Use S3 in production
USE_S3 = config('USE_S3', default=False, cast=bool)
if USE_S3:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'clickid',
        'TIMEOUT': 300,
    }
}


# Logging
LOG_DIR = Path(config('LOG_DIR', default=str(BASE_DIR / 'logs')))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'clickid.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'usuarios': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'coletas': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

