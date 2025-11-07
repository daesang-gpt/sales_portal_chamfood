"""
개발 환경 설정
"""

from .base import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%x$gh8s^ikq^5-rs$#%v%igig-+-j$9trc4(zx_bpe#t#j@m1z'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# URL 체크 비활성화 (dumpdata 실행 시 torch DLL 오류 방지)
import os
if os.environ.get('SKIP_URL_CHECKS', 'False').lower() == 'true':
    # URL 설정을 로드하지 않도록 임시로 비활성화
    pass

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '172.28.25.114', '*']

# Database - Oracle XE (개발용)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'localhost:1521/XEPDB1',  # Oracle PDB 연결
        'USER': 'salesportal',
        'PASSWORD': 'salesportal123',
        'HOST': '',  # NAME에 포함되어 있으므로 비워둠
        'PORT': '',  # NAME에 포함되어 있으므로 비워둠
    }
}

# 개발용 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
