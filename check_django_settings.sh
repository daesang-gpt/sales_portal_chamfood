#!/bin/bash

# Django 설정 확인 스크립트
# 사용법: ./check_django_settings.sh

cd /opt/sales-portal/backend

# 가상환경 활성화
source venv/bin/activate

# 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

echo "========================================"
echo "Django 설정 확인"
echo "========================================"
echo ""

echo "[1] BASE_DIR 확인:"
python manage.py shell -c "
from django.conf import settings
from pathlib import Path
print(f'BASE_DIR 타입: {type(settings.BASE_DIR)}')
print(f'BASE_DIR 값: {settings.BASE_DIR}')
print(f'BASE_DIR 문자열 변환: {str(settings.BASE_DIR)}')
" 2>&1

echo ""
echo "[2] STATIC_ROOT 확인:"
python manage.py shell -c "
from django.conf import settings
import os
print(f'STATIC_ROOT 설정됨: {\"STATIC_ROOT\" in dir(settings)}')
if hasattr(settings, 'STATIC_ROOT'):
    print(f'STATIC_ROOT 값: {settings.STATIC_ROOT}')
    print(f'STATIC_ROOT 타입: {type(settings.STATIC_ROOT)}')
    print(f'STATIC_ROOT 존재 여부: {os.path.exists(settings.STATIC_ROOT) if isinstance(settings.STATIC_ROOT, str) else \"경로가 문자열이 아님\"}')
else:
    print('❌ STATIC_ROOT가 설정되지 않았습니다!')
" 2>&1

echo ""
echo "[3] STATIC_URL 확인:"
python manage.py shell -c "
from django.conf import settings
print(f'STATIC_URL: {settings.STATIC_URL}')
" 2>&1

echo ""
echo "[4] settings.production.py 파일 확인:"
if [ -f "settings/production.py" ]; then
    echo "✅ settings/production.py 파일 존재"
    echo ""
    echo "STATIC_ROOT 관련 라인:"
    grep -n "STATIC_ROOT" settings/production.py || echo "  STATIC_ROOT를 찾을 수 없습니다"
else
    echo "❌ settings/production.py 파일이 없습니다"
fi

echo ""
echo "========================================"
echo "확인 완료"
echo "========================================"

