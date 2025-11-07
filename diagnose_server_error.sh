#!/bin/bash

# 서버 에러 진단 스크립트
# 사용법: ./diagnose_server_error.sh

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT/backend"

echo "========================================"
echo "서버 에러 진단 시작"
echo "========================================"
echo ""

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
if [ ! -d "venv" ]; then
    echo "❌ 가상환경을 찾을 수 없습니다"
    exit 1
fi

source venv/bin/activate

echo "[1/5] 데이터베이스 연결 확인..."
python manage.py shell -c "
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1 FROM DUAL')
    print('✅ 데이터베이스 연결 성공')
except Exception as e:
    print(f'❌ 데이터베이스 연결 실패: {e}')
" 2>&1

echo ""
echo "[2/5] Django 설정 확인..."
python manage.py shell -c "
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
print(f'SECRET_KEY 설정됨: {\"SECRET_KEY\" in dir(settings) and len(settings.SECRET_KEY) > 0}')
print(f'Database ENGINE: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
print(f'Database NAME: {settings.DATABASES[\"default\"][\"NAME\"]}')
print(f'Database USER: {settings.DATABASES[\"default\"][\"USER\"]}')
" 2>&1

echo ""
echo "[3/5] 마이그레이션 상태 확인..."
python manage.py showmigrations --plan 2>&1 | tail -20

echo ""
echo "[4/5] 정적 파일 확인..."
if [ -d "staticfiles" ]; then
    echo "✅ staticfiles 디렉토리 존재"
    STATIC_COUNT=$(find staticfiles -type f | wc -l)
    echo "   정적 파일 개수: $STATIC_COUNT"
else
    echo "⚠️  staticfiles 디렉토리가 없습니다"
    echo "   실행: python manage.py collectstatic --noinput"
fi

echo ""
echo "[5/5] 최근 로그 확인..."
if [ -f "$PROJECT_ROOT/logs/backend.log" ]; then
    echo "최근 에러 로그:"
    tail -n 50 "$PROJECT_ROOT/logs/backend.log" | grep -i -E "error|exception|traceback" | tail -10 || echo "  (에러 로그 없음)"
else
    echo "⚠️  로그 파일이 없습니다: $PROJECT_ROOT/logs/backend.log"
fi

echo ""
echo "========================================"
echo "추가 확인 사항"
echo "========================================"
echo ""
echo "1. 서버 프로세스 확인:"
ps aux | grep "manage.py runserver" | grep -v grep || echo "  서버가 실행 중이 아닙니다"

echo ""
echo "2. 포트 사용 확인:"
netstat -tuln | grep ":8000" || ss -tuln | grep ":8000" || echo "  포트 8000이 사용 중이 아닙니다"

echo ""
echo "3. 로그 파일 권한 확인:"
ls -lh "$PROJECT_ROOT/logs/" 2>/dev/null || echo "  로그 디렉토리를 확인할 수 없습니다"

echo ""
echo "========================================"
echo "진단 완료"
echo "========================================"

