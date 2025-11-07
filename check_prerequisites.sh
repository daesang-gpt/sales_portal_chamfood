#!/bin/bash

# 운영서버 시작 전 사전 준비사항 확인 스크립트
# 사용법: ./check_prerequisites.sh

set -e

PROJECT_ROOT="/opt/sales-portal"
ERRORS=0
WARNINGS=0

echo "========================================"
echo "사전 준비사항 확인 시작"
echo "========================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 체크 함수
check_pass() {
    echo -e "${GREEN}✅${NC} $1"
}

check_fail() {
    echo -e "${RED}❌${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# 1. 프로젝트 디렉토리 확인
echo "[1/10] 프로젝트 디렉토리 확인..."
if [ -d "$PROJECT_ROOT" ]; then
    check_pass "프로젝트 디렉토리 존재: $PROJECT_ROOT"
else
    check_fail "프로젝트 디렉토리가 없습니다: $PROJECT_ROOT"
    exit 1
fi

# 2. Backend 디렉토리 확인
echo "[2/10] Backend 디렉토리 확인..."
if [ -d "$PROJECT_ROOT/backend" ]; then
    check_pass "Backend 디렉토리 존재"
else
    check_fail "Backend 디렉토리가 없습니다: $PROJECT_ROOT/backend"
fi

# 3. Frontend 디렉토리 확인
echo "[3/10] Frontend 디렉토리 확인..."
if [ -d "$PROJECT_ROOT/frontend" ]; then
    check_pass "Frontend 디렉토리 존재"
else
    check_fail "Frontend 디렉토리가 없습니다: $PROJECT_ROOT/frontend"
fi

# 4. Backend 가상환경 확인
echo "[4/10] Backend 가상환경 확인..."
if [ -d "$PROJECT_ROOT/backend/venv" ]; then
    check_pass "Backend 가상환경 존재"
    
    # Python 실행 파일 확인
    if [ -f "$PROJECT_ROOT/backend/venv/bin/python" ]; then
        PYTHON_VERSION=$("$PROJECT_ROOT/backend/venv/bin/python" --version 2>&1)
        check_pass "Python 버전: $PYTHON_VERSION"
    else
        check_warn "가상환경에 Python 실행 파일이 없습니다"
    fi
else
    check_fail "Backend 가상환경이 없습니다: $PROJECT_ROOT/backend/venv"
fi

# 5. Frontend 빌드 확인
echo "[5/10] Frontend 빌드 확인..."
if [ -d "$PROJECT_ROOT/frontend/.next" ]; then
    check_pass "Frontend 빌드 파일 존재"
    BUILD_SIZE=$(du -sh "$PROJECT_ROOT/frontend/.next" 2>/dev/null | cut -f1)
    echo "   빌드 크기: $BUILD_SIZE"
else
    check_warn "Frontend 빌드 파일이 없습니다. 시작 시 자동 빌드됩니다."
fi

# 6. Node.js 및 npm 확인
echo "[6/10] Node.js 및 npm 확인..."
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js 설치됨: $NODE_VERSION"
else
    check_fail "Node.js가 설치되어 있지 않습니다"
fi

if command -v npm >/dev/null 2>&1; then
    NPM_VERSION=$(npm --version)
    check_pass "npm 설치됨: $NPM_VERSION"
else
    check_fail "npm이 설치되어 있지 않습니다"
fi

# 7. 포트 사용 여부 확인
echo "[7/10] 포트 사용 여부 확인..."

# Backend 포트 (8000)
if command -v netstat >/dev/null 2>&1; then
    PORT_8000=$(netstat -tuln 2>/dev/null | grep ":8000 " || true)
elif command -v ss >/dev/null 2>&1; then
    PORT_8000=$(ss -tuln 2>/dev/null | grep ":8000 " || true)
else
    PORT_8000=""
fi

if [ -n "$PORT_8000" ]; then
    check_warn "포트 8000이 이미 사용 중입니다"
    echo "   사용 중인 프로세스:"
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :8000 2>/dev/null | head -3 || echo "   (프로세스 정보 확인 불가)"
    else
        echo "   (lsof가 설치되어 있지 않아 프로세스 정보를 확인할 수 없습니다)"
    fi
else
    check_pass "포트 8000 사용 가능"
fi

# Frontend 포트 (3000)
if command -v netstat >/dev/null 2>&1; then
    PORT_3000=$(netstat -tuln 2>/dev/null | grep ":3000 " || true)
elif command -v ss >/dev/null 2>&1; then
    PORT_3000=$(ss -tuln 2>/dev/null | grep ":3000 " || true)
else
    PORT_3000=""
fi

if [ -n "$PORT_3000" ]; then
    check_warn "포트 3000이 이미 사용 중입니다"
    echo "   사용 중인 프로세스:"
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :3000 2>/dev/null | head -3 || echo "   (프로세스 정보 확인 불가)"
    else
        echo "   (lsof가 설치되어 있지 않아 프로세스 정보를 확인할 수 없습니다)"
    fi
else
    check_pass "포트 3000 사용 가능"
fi

# 8. Oracle 환경변수 확인
echo "[8/10] Oracle 환경변수 확인..."
if [ -n "$ORACLE_HOME" ]; then
    check_pass "ORACLE_HOME 설정됨: $ORACLE_HOME"
    if [ -d "$ORACLE_HOME" ]; then
        check_pass "ORACLE_HOME 디렉토리 존재"
    else
        check_warn "ORACLE_HOME 디렉토리가 존재하지 않습니다: $ORACLE_HOME"
    fi
else
    check_warn "ORACLE_HOME 환경변수가 설정되어 있지 않습니다"
    echo "   스크립트에서 자동으로 설정됩니다"
fi

# 9. 데이터베이스 연결 확인
echo "[9/10] 데이터베이스 연결 확인..."
cd "$PROJECT_ROOT/backend"

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
    
    # 환경변수 설정
    export DJANGO_SETTINGS_MODULE=settings.production
    export DB_NAME=192.168.99.37:1521/XEPDB1
    export DB_USER=salesportal
    export DB_PASSWORD=salesportal123
    
    # Oracle 환경변수 설정
    export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
    export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
    export PATH=$ORACLE_HOME/bin:$PATH
    
    # DB 연결 테스트
    if python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('OK')" >/dev/null 2>&1; then
        check_pass "데이터베이스 연결 성공"
    else
        check_fail "데이터베이스 연결 실패"
        echo "   연결 정보를 확인하세요:"
        echo "   - DB_NAME: $DB_NAME"
        echo "   - DB_USER: $DB_USER"
        echo "   - ORACLE_HOME: $ORACLE_HOME"
    fi
else
    check_warn "가상환경이 없어 데이터베이스 연결을 확인할 수 없습니다"
fi

# 10. 실행 스크립트 확인
echo "[10/10] 실행 스크립트 확인..."
SCRIPTS=("start_backend_daemon.sh" "start_frontend_daemon.sh" "start_all_daemon.sh" "stop_backend.sh" "stop_frontend.sh" "stop_all.sh" "status.sh")

for script in "${SCRIPTS[@]}"; do
    if [ -f "$PROJECT_ROOT/$script" ]; then
        if [ -x "$PROJECT_ROOT/$script" ]; then
            check_pass "$script 실행 가능"
        else
            check_warn "$script 실행 권한이 없습니다"
            echo "   실행 권한 부여: chmod +x $PROJECT_ROOT/$script"
        fi
    else
        check_warn "$script 파일이 없습니다"
    fi
done

# 로그 디렉토리 확인
echo ""
echo "[추가] 로그 디렉토리 확인..."
if [ -d "$PROJECT_ROOT/logs" ]; then
    check_pass "로그 디렉토리 존재"
    LOG_SIZE=$(du -sh "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1)
    echo "   로그 디렉토리 크기: $LOG_SIZE"
else
    check_warn "로그 디렉토리가 없습니다. 시작 시 자동 생성됩니다."
fi

# 결과 요약
echo ""
echo "========================================"
echo "확인 완료"
echo "========================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 확인 항목이 통과되었습니다!${NC}"
    echo "서버를 시작할 수 있습니다: ./start_all_daemon.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  경고가 $WARNINGS개 있습니다.${NC}"
    echo "대부분의 경우 서버를 시작할 수 있지만, 경고 사항을 확인하세요."
    echo "서버 시작: ./start_all_daemon.sh"
    exit 0
else
    echo -e "${RED}❌ 오류가 $ERRORS개 있습니다.${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  경고가 $WARNINGS개 있습니다.${NC}"
    fi
    echo "오류를 해결한 후 다시 시도하세요."
    exit 1
fi

