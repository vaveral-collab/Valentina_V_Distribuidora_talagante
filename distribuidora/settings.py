import os
from pathlib import Path
from django.contrib.messages import constants as messages

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

LOGIN_URL = '/login/'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'Pudu_supremo_django_talagante_2026_chacareromeOwlmeOwl_k9m4q8r5t1v3w6y0z2b5n8j0'

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = os.environ.get('DEBUG', 'False') == 'True'
DEBUG = True

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',       
    'core',
    'rest_framework',
    'django.contrib.humanize', # Importante para los precios
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'distribuidora.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

WSGI_APPLICATION = 'distribuidora.wsgi.application'


# ====================== CONFIGURACIÓN DE BASE DE DATOS ======================

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback para desarrollo local (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if 'db' in DATABASES['default'].get('HOST', ''):
    DATABASES['default']['NAME'] = 'distribuidora_db'
    DATABASES['default']['USER'] = 'pudu_supremo'
    DATABASES['default']['PASSWORD'] = 'pUdu5itO1403'
    DATABASES['default']['HOST'] = 'db'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =================================================
# CONFIGURACIÓN DE IDIOMA Y FORMATO DE PRECIOS
# =================================================

LANGUAGE_CODE = 'es-cl' # Español Chile

TIME_ZONE = 'America/Santiago' # Hora de Chile

USE_I18N = True

USE_TZ = True

# ESTO ES LO QUE HACE QUE SALGA $10.000 (Puntos en miles)
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
NUMBER_GROUPING = 3

# ====================== STATIC FILES ======================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# ====================== MEDIA FILES ======================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de storages (Django 4.2+ recomendado)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",  # ← almacenamiento local (disco del VPS)
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",  # ← sigue igual, es bueno
    },
}


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Validación Correo
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'fabriicratos10@gmail.com'
EMAIL_HOST_PASSWORD = 'ownr xwfg tkgh uqnl'
DEFAULT_FROM_EMAIL = 'Distribuidora Talagante <fabriicratos10@gmail.com>'


DEFAULT_FROM_EMAIL = 'Distribuidora Talagante <no-reply@distribuidoratoralagante.cl>'
SERVER_EMAIL = 'Distribuidora Talagante <no-reply@distribuidoratoralagante.cl>'

# Configuración de Mensajes (Alertas)
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '187.77.33.165',                        # tu IP del VPS
    'distribuidoratalagante.cloud',         # tu dominio principal
    'www.distribuidoratalagante.cloud',
]
# ---------- SEGURIDAD Y HOSTS ----------
#DEBUG = os.environ.get('DEBUG', 'False') == 'True'
#ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Si estás en Render, agrega automáticamente el host dinámico
#if 'RENDER'in os.environ:
    #ALLOWED_HOSTS.append(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))
# CSRF y seguridad para producción con HTTPS
CSRF_TRUSTED_ORIGINS = [
    'https://distribuidoratalagante.cloud',
    'https://www.distribuidoratalagante.cloud',
]
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    

