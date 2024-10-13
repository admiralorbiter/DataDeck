"""
Django settings for engagekc project.

Generated by 'django-admin startproject' using Django 5.0.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import sys
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug prints
print("DB_HOST:", os.environ.get('DB_HOST'))
print("DB_NAME:", os.environ.get('DB_NAME'))
print("DB_USER:", os.environ.get('DB_USER'))
print("DB_PASSWORD:", os.environ.get('DB_PASSWORD'))
print("DB_PORT:", os.environ.get('DB_PORT'))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4iaw(8^ug^+h5jqiu$bir-0zr(u0gv6(1rgfw#p4cny=96uy1s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGIN_REDIRECT_URL = '/'

# Celery Configuration Options
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Example using Redis as the message broker
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CELERY_BEAT_SCHEDULE = {
    'clear-expired-sessions-every-day': {
        'task': 'video_app.tasks.clear_expired_sessions',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
    },
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ALLOWED_HOSTS = [
    '127.0.0.1', 'localhost',
    'da1e4a43-a582-482a-9f0b-0ff075e026ca-00-44w0qiqqdybg.worf.replit.dev',
    '42d4b43d-020c-4c8f-825a-792d21945254-00-1vdpmgorpm3kr.picard.replit.dev',
    'https://42d4b43d-020c-4c8f-825a-792d21945254-00-1vdpmgorpm3kr.picard.replit.dev',
    'jlane.pythonanywhere.com',
    'datadeck.dev',
    'www.datadeck.dev',
    'webapp-2258943.pythonanywhere.com'
]

CSRF_TRUSTED_ORIGINS = [
    'https://da1e4a43-a582-482a-9f0b-0ff075e026ca-00-44w0qiqqdybg.worf.replit.dev',
    'https://jlane.pythonanywhere.com',
    'https://42d4b43d-020c-4c8f-825a-792d21945254-00-1vdpmgorpm3kr.picard.replit.dev'
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'video_app.apps.VideoAppConfig',
    'widget_tweaks',
    'pytest_django',
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

ROOT_URLCONF = 'engagekc.urls'

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
                'video_app.views.nav_sessions',
            ],
        },
    },
]

WSGI_APPLICATION = 'engagekc.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

USE_MYSQL = os.environ.get('USE_MYSQL', 'TRUE').upper() == 'TRUE'

if USE_MYSQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'jlane$datadeck'),
            'USER': os.environ.get('DB_USER', 'jlane'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'Thisisapassword#1'),
            'HOST': os.environ.get('DB_HOST', 'jlane.mysql.pythonanywhere-services.com'),
            'PORT': os.environ.get('DB_PORT', '3306'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Use a separate test database when running tests
if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

AUTH_USER_MODEL = 'video_app.CustomAdmin'

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'

# Add this if you want to collect static files into a single directory (e.g., for deployment)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'video_app/static'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Test-specific settings
if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    DEBUG = True
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
