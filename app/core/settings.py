"""
Django settings for MargaBackend project.

Generated by 'django-admin startproject' using Django 3.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
from celery.schedules import crontab
from django.utils.translation import ugettext_lazy as _

import os

from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '7-z)z9au&-onqqr8e_ho!&qd+0&+@&@t=bkhxavowp7o@hxp_9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    os.environ.get('DJANGO_DOMAIN'),
    '127.0.0.1'
]
DOMAIN = os.environ.get('DJANGO_DOMAIN')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',

    'celery',
    'django_extensions',
    'drf_yasg',
    'rest_framework',

    'users',
    'notifications',
    'pdf',
    'common'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'
LANGUAGES = (
    ('ru-ru', _('Russian')),
    ('en', _('English')),
)
TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/media/'

SHELL_PLUS = "ipython"


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.JWTAuthentication',
    ),
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%S",
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

SIMPLE_JWT = {
    'SLIDING_TOKEN_LIFETIME': timedelta(days=1),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1)
}

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    'APIS_SORTER': 'alpha',
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    'OPERATIONS_SORTER': 'alpha'
}

if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()]
    )


LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = os.getenv('RABBITMQ_DSN')
CELERY_RESULT_BACKEND = None
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_IGNORE_RESULT = True

CELERY_BEAT_SCHEDULE = {
    'task_every_day': {
        'task': 'common.tasks.task_every_day',
        'schedule': crontab(minute=0, hour=0),
    }
}

SUPERUSER_NAME = os.getenv('SUPERUSER_NAME')
SUPERUSER_PASSWORD = os.getenv('SUPERUSER_PASSWORD')

# -- Notification settings
NOTIFICATION_TEMPLATES = '/app/templates'
SMSPROSTO_URL = 'http://api.sms-prosto.ru/'
PHONE_REGISTRATION_CODE_LIFETIME = 5*60
EMAIL_REGISTRATION_CODE_LIFETIME = 24*60*60

SMSPROSTO_KEY = os.getenv('SMSPROSTO_KEY')

# -- Document settings -----------
PREVIEW_WIDTH = int(os.getenv('PREVIEW_WIDTH'))
PREVIEW_HEIGHT = int(os.getenv('PREVIEW_HEIGHT'))


# -- Unione settings --------------
EMAIL_NOTIFICATIONS = True
EMAIL_API_KEY = '6w3pxxie66qzym1kc4pqnrzquxy5ux194jfkji5o'
EMAIL_HOST = 'https://eu1.unione.io'
EMAIL_PORT = 465
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_SUBJECT_PREFIX = ''
EMAIL_TEMPLATE_ENGINE = 'simple'
EMAIL_REPLY_TO = ''
EMAIL_TEMPLATES = {}
# --- ?????????? ???????????????? ?????????????????? ???????????????? --
SERVER_EMAIL = 'noreply@marga.app'
# --- ??????????, ?? ???????????????? ?????????? ?????????????? ???????????? ???????????????? ?????????? --
FEEDBACK_EMAIL = 'feedback@marga.app'
# --- ??????????, ???? ?????????????? ?????????? ?????????????????? ???????????????? ?????????? ???? ????????????????. ?????????? ???????????????? ?? ???????????????????? --
ADMIN_EMAIL = 'ivanperovsky@gmail.com'
SERVER_EMAIL_NAME = 'PDF Converter'


