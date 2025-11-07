#!/bin/bash
# Django 정적 파일 수집 및 설정 스크립트
# 사용법: ./setup_static_files.sh

set -e

echo "========================================"
echo "Django 정적 파일 설정 시작..."
echo "========================================"

cd /opt/sales-portal/backend

# 가상환경 활성화
source venv/bin/activate

# 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export SECRET_KEY=${SECRET_KEY:-your-production-secret-key-here}
export ALLOWED_HOSTS=${ALLOWED_HOSTS:-192.168.99.37,dslspdev}
export DB_NAME=${DB_NAME:-192.168.99.37:1521/XEPDB1}
export DB_USER=${DB_USER:-salesportal}
export DB_PASSWORD=${DB_PASSWORD:-salesportal123}
export SERVE_STATIC=true  # 정적 파일 서빙 활성화

# Oracle 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

echo "[1] STATIC_ROOT 확인..."
python manage.py shell -c "
from django.conf import settings
import os
print(f'STATIC_ROOT: {settings.STATIC_ROOT}')
print(f'STATIC_URL: {settings.STATIC_URL}')
print(f'STATIC_ROOT 존재 여부: {os.path.exists(settings.STATIC_ROOT)}')
" 2>&1

echo ""
echo "[2] 정적 파일 수집 (collectstatic)..."
python manage.py collectstatic --noinput --clear

echo ""
echo "[3] 수집된 정적 파일 확인..."
if [ -d "staticfiles" ]; then
    STATIC_COUNT=$(find staticfiles -type f | wc -l)
    echo "✅ staticfiles 디렉토리 존재"
    echo "   정적 파일 개수: $STATIC_COUNT"
    
    # 주요 파일 확인
    echo ""
    echo "주요 정적 파일 확인:"
    if [ -f "staticfiles/admin/css/base.css" ]; then
        echo "  ✅ admin/css/base.css 존재"
    else
        echo "  ⚠️  admin/css/base.css 없음"
    fi
    
    if [ -f "staticfiles/admin/js/core.js" ]; then
        echo "  ✅ admin/js/core.js 존재"
    else
        echo "  ⚠️  admin/js/core.js 없음"
    fi
else
    echo "❌ staticfiles 디렉토리가 없습니다!"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ 정적 파일 설정 완료!"
echo "========================================"
echo ""
echo "다음 단계:"
echo "1. Django 서버 재시작"
echo "2. 환경변수 SERVE_STATIC=true 설정 확인"
echo "3. 브라우저에서 http://192.168.99.37:8000/admin/ 접속하여 확인"
echo ""
echo "참고: 운영 환경에서는 웹 서버(Nginx 등)에서 정적 파일을 제공하는 것이 권장됩니다."

