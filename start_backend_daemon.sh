#!/bin/bash

# 운영서버용 Django Backend 백그라운드 실행 스크립트
# SSH 세션이 끊어져도 계속 실행됩니다

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT/backend"

# 이미 실행 중인지 확인
if pgrep -f "manage.py runserver" > /dev/null; then
    echo "⚠️  Backend가 이미 실행 중입니다."
    echo "   중지하려면: ./stop_backend.sh"
    exit 1
fi

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
export SERVE_STATIC=true  # 정적 파일 서빙 활성화

# Python 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경을 찾을 수 없습니다: $PROJECT_ROOT/backend/venv"
    exit 1
fi

source venv/bin/activate

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

# 로그 파일 권한 설정 (이미 존재하는 경우)
if [ -f "$PROJECT_ROOT/logs/backend.log" ]; then
    chmod 644 "$PROJECT_ROOT/logs/backend.log" 2>/dev/null || true
fi

# umask 설정 (로그 파일이 읽기 가능하도록)
umask 022

echo "========================================"
echo "Django Backend 백그라운드 시작 중..."
echo "========================================"
echo "서버 주소: http://192.168.99.37:8000"
echo "로그 파일: $PROJECT_ROOT/logs/backend.log"
echo ""

# 백그라운드에서 실행 (nohup 사용)
nohup python manage.py runserver 0.0.0.0:8000 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &

# 프로세스 ID 저장
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"

# 로그 파일 권한 명시적 설정
sleep 1
chmod 644 "$PROJECT_ROOT/logs/backend.log" 2>/dev/null || true
chmod 644 "$PROJECT_ROOT/logs/backend.pid" 2>/dev/null || true

echo "✅ Backend가 백그라운드에서 시작되었습니다."
echo "   PID: $BACKEND_PID"
echo "   로그 확인: tail -f $PROJECT_ROOT/logs/backend.log"
echo "   중지: ./stop_backend.sh"
echo "   상태 확인: ./status.sh"
echo ""

# 잠시 대기 후 상태 확인
sleep 2
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend가 정상적으로 실행 중입니다."
else
    echo "⚠️  Backend 시작에 실패했을 수 있습니다. 로그를 확인하세요:"
    echo "   tail -n 50 $PROJECT_ROOT/logs/backend.log"
    exit 1
fi

