가""
PostgreSQL 데이터 백업용 임시 설정
"""

from .base import *

# SECRET_KEY 설정
SECRET_KEY = 'django-insecure-%x$gh8s^ikq^5-rs$#%v%igig-+-j$9trc4(zx_bpe#t#j@m1z'

# PostgreSQL 데이터베이스 설정
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'salesportal',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
