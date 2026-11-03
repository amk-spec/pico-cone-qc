"""Development prototype. All decisions are simulations, never production authorization."""
import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from urllib.parse import urlparse, unquote, parse_qs

BASE_DIR = Path(__file__).resolve().parent.parent
HOSTED_PREVIEW = os.environ.get('LANDER_HOSTED_PREVIEW') == '1'
LOCAL_DIR = Path(os.environ.get('LANDER_DATA_DIR', str(BASE_DIR / '.local')))
if os.environ.get('QC_USE_SQLITE') == '1':
    LOCAL_DIR = LOCAL_DIR / 'sqlite-review'
if not HOSTED_PREVIEW:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
if HOSTED_PREVIEW and (not os.environ.get('DJANGO_SECRET_KEY') or len(os.environ['DJANGO_SECRET_KEY']) < 50):
    raise ImproperlyConfigured('Hosted preview needs a strong DJANGO_SECRET_KEY configured securely by the hosting service.')
key_path = LOCAL_DIR / 'django-secret'
if not HOSTED_PREVIEW and not os.environ.get('DJANGO_SECRET_KEY') and not key_path.exists():
    import secrets
    key_path.write_text(secrets.token_urlsafe(64))
    key_path.chmod(0o600)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or key_path.read_text()
DEBUG = not HOSTED_PREVIEW and os.environ.get('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],testserver').split(',')
if HOSTED_PREVIEW:
    hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', os.environ.get('RENDER_EXTERNAL_HOSTNAME', ''))
    ALLOWED_HOSTS = [h.strip() for h in hosts.split(',') if h.strip()]
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('Hosted preview requires an explicit preview hostname, not a wildcard.')
CSRF_TRUSTED_ORIGINS = [v for v in os.environ.get('DJANGO_CSRF_ORIGINS', '').split(',') if v]
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'qc', 'axes']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware', 'axes.middleware.AxesMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages', 'qc.context.navigation']}}]
WSGI_APPLICATION = 'config.wsgi.application'
url = os.environ.get('DATABASE_URL', '')
if HOSTED_PREVIEW and (not url or os.environ.get('QC_USE_SQLITE') == '1'):
    raise ImproperlyConfigured('Hosted preview requires DATABASE_URL for a dedicated PostgreSQL database.')
if not HOSTED_PREVIEW and not url and (LOCAL_DIR / 'database-url').exists():
    url = (LOCAL_DIR / 'database-url').read_text().strip()
if os.environ.get('QC_USE_SQLITE') == '1':
    url = ''
if url:
    p = urlparse(url)
    if p.scheme not in ('postgres', 'postgresql'):
        raise ValueError('DATABASE_URL must use PostgreSQL')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': unquote(p.path.lstrip('/')), 'USER': unquote(p.username or ''), 'PASSWORD': unquote(p.password or ''), 'HOST': parse_qs(p.query).get('host', [p.hostname or ''])[0], 'PORT': p.port or 5432, 'OPTIONS': {key: values[0] for key, values in parse_qs(p.query).items() if key in ('sslmode','sslrootcert','sslcert','sslkey')}}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': LOCAL_DIR / 'prototype.sqlite3', 'OPTIONS': {'timeout': 20}}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' if HOSTED_PREVIEW else LOCAL_DIR / 'static'
MEDIA_ROOT = LOCAL_DIR / 'evidence'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 14 * 1024 * 1024
PROTOTYPE = True

# The hosted mode remains a prototype, with synthetic data and no engineering approval.
AUTHENTICATION_BACKENDS = ['axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend']
AXES_ENABLED = HOSTED_PREVIEW
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_RESET_ON_SUCCESS = True
AXES_HTTP_RESPONSE_CODE = 429
AXES_LOCKOUT_TEMPLATE = 'registration/locked.html'
AXES_VERBOSE = False
AXES_SENSITIVE_PARAMETERS = ['username', 'ip_address']
if HOSTED_PREVIEW:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r'^health/$']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SESSION_COOKIE_AGE = 60 * 60 * 4
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }

if os.environ.get('LANDER_BUILD') == '1':
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }
