import os 
from pathlib import Path
from datetime import timedelta
import logging.config
from urllib.parse import quote
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import credentials, get_app, initialize_app
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ('true', '1', 'yes')


def env_list(name, default=''):
    return [value.strip() for value in os.environ.get(name, default).split(',') if value.strip()]


def redis_url():
    configured_url = os.environ.get('REDIS_URL')
    if configured_url:
        return configured_url

    host = os.environ.get('REDIS_HOST', 'redis')
    port = os.environ.get('REDIS_PORT', '6379')
    password = os.environ.get('REDIS_PASSWORD')
    authentication = f':{quote(password)}@' if password else ''
    return f'redis://{authentication}{host}:{port}/0'


SECRET_KEY = os.environ.get('DJANGO_SECRET')
if not SECRET_KEY:
    raise ImproperlyConfigured('DJANGO_SECRET must be configured.')

DEBUG = env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEBUG else '')
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must be configured when DJANGO_DEBUG=False.')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000' if not DEBUG else '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True




LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

logging.config.dictConfig(LOGGING)



INSTALLED_APPS = [
    "daphne",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'clients', 
    'drivers', 
    'rides', 
    'conversation', 
    'support', 
    'core',
    'notifications', 
    'referrals', 
    'payments', 
    'promotions', 
    'navigation', 
    'channels', 
    'backoffice', 
    'rest_framework', 
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders', 
    "fcm_django", 
    'django_celery_beat', 

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', DEBUG)
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

SPECTACULAR_SETTINGS = {
    'TITLE': 'TOYA  API ',
    'DESCRIPTION': """The Toya API is a complete solution for connecting private drivers and customers,
    designed to manage all the operations of a transport platform. """,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'bearerAuth': []}], 
}



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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

AUTH_USER_MODEL = "core.BaseUser"


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    "SIGNING_KEY": SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# FIREBASE
FIREBASE_CREDENTIALS = os.environ.get(
    'FIREBASE_CREDENTIALS',
    os.path.join(BASE_DIR, 'core', 'firebase', 'serviceAccountKey.json'),
)

try:
    get_app()
except ValueError:
    initialize_app(credentials.Certificate(FIREBASE_CREDENTIALS))


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases



ASGI_APPLICATION = "core.asgi.application"

# WSGI_APPLICATION = 'core.wsgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
             "hosts": [redis_url()],
        },
    },
}



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', os.environ.get('POSTGRES_DB', 'toya_db')),
        'USER': os.environ.get('DB_USER', os.environ.get('POSTGRES_USER', 'toya')),
        'PASSWORD': os.environ.get('DB_PASSWORD', os.environ.get('POSTGRES_PASSWORD', '')),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }
}




# Celery settings

CELERY_BROKER_URL = redis_url()
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'






# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels.layers.InMemoryChannelLayer',
#         'CONFIG': {},
#     },
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / "db.sqlite3",
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.environ.get('TIME_ZONE', 'Africa/Douala')

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/


STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATIC_ROOT = os.environ.get('STATIC_ROOT', '/vol/static')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/vol/media')


GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')


# ============================================================================
# OTP SIGNUP VERIFICATION FEATURE FLAGS
# ============================================================================
# These flags control the OTP signup verification feature for safe rollback.
# Set via environment variables or defaults to False for backward compatibility.

# ENFORCE_PHONE_VERIFICATION: When True, requires phone verification before login
# When False (default): Registration issues tokens immediately (legacy behavior)
ENFORCE_PHONE_VERIFICATION = os.environ.get('ENFORCE_PHONE_VERIFICATION', 'False').lower() in ('true', '1', 'yes')

# ENABLE_OTP_THROTTLING: When True, applies rate limiting to OTP endpoints
# When False: Disables throttling (useful for testing or emergency situations)
# Throttle rates are configured in core/throttling.py
ENABLE_OTP_THROTTLING = os.environ.get('ENABLE_OTP_THROTTLING', 'True').lower() in ('true', '1', 'yes')


# ============================================================================
# TESTING & DEVELOPMENT ENDPOINTS FEATURE FLAG
# ============================================================================
# ⚠️ CRITICAL SECURITY SETTING ⚠️
# This flag controls access to destructive testing endpoints that can:
#   - Delete user accounts and all related data
#   - Reset accounts to initial state (clear rides, payments, etc.)
#   - Adjust driver wallet balances arbitrarily
#
# ENABLE_TESTING_ENDPOINTS: When True, enables development testing endpoints
# When False (default): All testing endpoints return 403 Forbidden
#
# 🔴 MUST BE FALSE IN PRODUCTION 🔴
# These endpoints bypass normal business logic and can cause data loss.
# Only enable in local development or isolated testing environments.
#
# Affected endpoints:
#   - POST /clients/dev/reset/          (clears all client data)
#   - DELETE /clients/delete/           (permanently deletes client)
#   - POST /drivers/dev/reset/          (clears all driver data)
#   - POST /drivers/dev/adjust-wallet/  (sets arbitrary wallet balance)
#   - DELETE /drivers/delete/           (permanently deletes driver)
#
# Set via environment variable or manually in settings:
#   export ENABLE_TESTING_ENDPOINTS=true   # Enable for testing
#   export ENABLE_TESTING_ENDPOINTS=false  # Disable for production (default)
#
ENABLE_TESTING_ENDPOINTS = os.environ.get('ENABLE_TESTING_ENDPOINTS', 'False').lower() in ('true', '1', 'yes')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
