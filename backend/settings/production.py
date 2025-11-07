"""
운영 환경 설정
"""

from .base import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database - Oracle (운영용)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ.get('DB_NAME', 'localhost:1521/XEPDB1'),
        'USER': os.environ.get('DB_USER', 'salesportal'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'salesportal123'),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

# 보안 설정
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files 설정 (운영용)
# BASE_DIR이 Path 객체이므로 명시적으로 절대 경로 문자열로 변환
# backend 디렉토리 안에 staticfiles 생성
STATIC_ROOT = os.path.abspath(os.path.join(str(BASE_DIR), 'backend', 'staticfiles'))

# 운영 환경에서 개발 서버를 사용하는 경우 정적 파일 서빙 활성화
# 실제 운영 환경에서는 웹 서버(Nginx 등)에서 정적 파일을 제공하는 것이 권장됨
# 환경변수 SERVE_STATIC=true로 설정하면 정적 파일 서빙 활성화

# 로깅 설정 (운영용)
# 로그 디렉토리 생성 (없으면 자동 생성)
LOG_DIR = str(BASE_DIR / 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{levelname} {asctime} {pathname}:{lineno} {funcName} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django_error.log'),
            'formatter': 'detailed',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
