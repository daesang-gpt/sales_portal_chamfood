#!/bin/bash
# 정적 파일 문제 진단 스크립트

echo "========================================"
echo "정적 파일 문제 진단"
echo "========================================"
echo ""

# 1. 정적 파일 디렉토리 확인
echo "[1] 정적 파일 디렉토리 확인..."
STATIC_ROOT="/opt/sales-portal/backend/staticfiles"
if [ -d "$STATIC_ROOT" ]; then
    echo "✅ 디렉토리 존재: $STATIC_ROOT"
    FILE_COUNT=$(find "$STATIC_ROOT" -type f | wc -l)
    echo "   파일 개수: $FILE_COUNT"
    
    # 주요 파일 확인
    if [ -f "$STATIC_ROOT/admin/css/base.css" ]; then
        echo "   ✅ admin/css/base.css 존재"
    else
        echo "   ❌ admin/css/base.css 없음"
    fi
else
    echo "❌ 디렉토리 없음: $STATIC_ROOT"
fi

echo ""

# 2. Django 설정 확인
echo "[2] Django 설정 확인..."
cd /opt/sales-portal/backend
source venv/bin/activate 2>/dev/null || true
export DJANGO_SETTINGS_MODULE=settings.production
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH

python manage.py shell -c "
from django.conf import settings
import os
print(f'STATIC_ROOT: {settings.STATIC_ROOT}')
print(f'STATIC_URL: {settings.STATIC_URL}')
print(f'DEBUG: {settings.DEBUG}')
print(f'STATIC_ROOT 존재: {os.path.exists(settings.STATIC_ROOT)}')
" 2>&1

echo ""

# 3. 실행 중인 Django 프로세스 확인
echo "[3] 실행 중인 Django 프로세스 확인..."
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "✅ Django 서버 실행 중"
    PID=$(pgrep -f "manage.py runserver" | head -1)
    echo "   PID: $PID"
    
    # 환경변수 확인
    echo "   환경변수 확인:"
    cat /proc/$PID/environ 2>/dev/null | tr '\0' '\n' | grep -E "SERVE_STATIC|DJANGO_SETTINGS" || echo "   (환경변수 확인 불가)"
else
    echo "❌ Django 서버가 실행 중이지 않습니다"
fi

echo ""

# 4. 정적 파일 URL 테스트
echo "[4] 정적 파일 접근 테스트..."
if command -v curl &> /dev/null; then
    echo "   테스트 URL: http://192.168.99.37:8000/static/admin/css/base.css"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://192.168.99.37:8000/static/admin/css/base.css 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ 정적 파일 접근 가능 (HTTP $HTTP_CODE)"
    else
        echo "   ❌ 정적 파일 접근 불가 (HTTP $HTTP_CODE)"
    fi
else
    echo "   ⚠️  curl이 설치되어 있지 않습니다"
fi

echo ""

# 5. 방화벽 확인
echo "[5] 방화벽 포트 확인..."
if command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --list-ports 2>/dev/null | grep -q "8000"; then
        echo "   ✅ 8000 포트 열림"
    else
        echo "   ⚠️  8000 포트가 방화벽에서 열려있지 않을 수 있습니다"
    fi
elif command -v iptables &> /dev/null; then
    if iptables -L -n 2>/dev/null | grep -q "8000"; then
        echo "   ✅ 8000 포트 관련 규칙 존재"
    else
        echo "   ⚠️  8000 포트 규칙 확인 필요"
    fi
else
    echo "   ⚠️  방화벽 도구를 찾을 수 없습니다"
fi

echo ""
echo "========================================"
echo "진단 완료"
echo "========================================"
echo ""
echo "해결 방법:"
echo "1. 정적 파일 수집: cd /opt/sales-portal/backend && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=settings.production && python manage.py collectstatic --noinput"
echo "2. SERVE_STATIC=true 환경변수 설정 확인"
echo "3. Django 서버 재시작: cd /opt/sales-portal && ./stop_backend.sh && ./start_backend_daemon.sh"
echo ""

