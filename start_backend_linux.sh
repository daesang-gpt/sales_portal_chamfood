#!/bin/bash

# 운영서버용 Django Backend 시작 스크립트
# Oracle Linux 8.6 + Oracle 19c

# 스크립트 실행 위치로 이동
cd /opt/sales-portal/backend

# Oracle 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

# Django 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export SECRET_KEY=your-production-secret-key-here
export ALLOWED_HOSTS=192.168.99.37,dslspdev
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# Python 가상환경 활성화
source venv/bin/activate

echo "Django Backend 시작 중..."
echo "서버 주소: http://192.168.99.37:8000"
echo "로그 파일: backend.log"

# Django 서버 시작
python manage.py runserver 0.0.0.0:8000
