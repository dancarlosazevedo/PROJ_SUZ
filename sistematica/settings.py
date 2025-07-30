import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurações de Segurança e Ambiente ---
# Pega a SECRET_KEY do arquivo .env
SECRET_KEY = config('SECRET_KEY')

# O modo DEBUG é controlado pelo .env (ex: DEBUG=True ou DEBUG=False)
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS é lido como uma lista de strings do .env
# Exemplo no .env: ALLOWED_HOSTS=localhost,127.0.0.1,projsuz-production.up.railway.app
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


# --- Aplicações Django ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps locais
    'core',
    # Libs externas
    'simple_history',
]

# --- Middleware ---
# A ordem é importante
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise deve vir logo após o SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

# --- Configuração de URLs e Aplicação ---
ROOT_URLCONF = 'sistematica.urls'
WSGI_APPLICATION = 'sistematica.wsgi.application'

# ... (depois da linha WSGI_APPLICATION)

# --- Templates ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Adiciona um diretório de templates na raiz do projeto, se você precisar
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# --- Banco de Dados ---
# Configuração feita via DATABASE_URL do arquivo .env usando dj-database-url
# Garante que a URL no .env use o nome do serviço do Docker (ex: @sistematica_db:5432)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}


# --- Validação de Senhas ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]


# --- Internacionalização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- Arquivos Estáticos (Static Files) ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Melhora a performance e o cache dos arquivos estáticos em produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --- Arquivos de Mídia (Media Files) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- Configurações Específicas de Ambiente (ex: Railway) ---
if os.getenv("RAILWAY_ENVIRONMENT"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Chave Primária Padrão ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'