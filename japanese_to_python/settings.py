"""
Django settings for japanese_to_python project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key')
DEBUG = config('DEBUG', default=False, cast=bool)

RAILWAY_ENVIRONMENT = os.environ.get('RAILWAY_ENVIRONMENT', 'False').lower() in ['true', '1', 'yes']

# Railway環境判定後の設定
if RAILWAY_ENVIRONMENT:
    CSRF_TRUSTED_ORIGINS = [
        f'https://{host}' for host in ALLOWED_HOSTS if host != 'localhost'
    ] + ['http://localhost:8000']
    DEBUG = False  # 本番環境では必ずFalseに
else:
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.railway.app'  # Railwayのデフォルトドメインをカバー
]

if RAILWAY_ENVIRONMENT:
    CSRF_TRUSTED_ORIGINS = [
        f'https://{host}' for host in ALLOWED_HOSTS if host != 'localhost'
    ] + ['http://localhost:8000']
else:
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'converter',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoiseを先頭に近く
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Security enhancements
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1年間
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

ROOT_URLCONF = 'japanese_to_python.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'converter/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': ['django.templatetags.static'],  # テンプレートでの静的ファイル参照を簡略化
        },
    },
]

WSGI_APPLICATION = 'japanese_to_python.wsgi.application'

# 修正後のデータベース設定
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', 'sqlite:///' + str(BASE_DIR / 'db.sqlite3')),
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

# エラーチェック用のコードを追加
if not DATABASES['default']:  # データベース設定が空の場合
    raise ValueError('Database configuration error! Check DATABASE_URL')

# SQLite用のフォールバック設定（PostgreSQL接続時は無視）
if 'sqlite' in DATABASES['default'].get('ENGINE', ''):
    DATABASES['default']['OPTIONS'] = {
        'timeout': 20,
    }
    
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# Static files configuration for Railway
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'converter/static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Whitenoise compression
WHITENOISE_MANIFEST_STRICT = False  # Railway環境での安定性向上

# Media files (必要に応じて)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Railway用の追加設定
if RAILWAY_ENVIRONMENT:
    # 静的ファイルの自動検出を無効化
    WHITENOISE_AUTOREFRESH = True
    # プロキシ設定
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    