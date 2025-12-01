#!/bin/bash

# ⚠️⚠️⚠️ 경고: 운영 서버 완전 삭제 스크립트 (서버에서 직접 실행) ⚠️⚠️⚠️
# 이 스크립트는 서버에서 직접 실행해야 합니다.
# 사용법: 서버에 SSH 접속 후 이 스크립트를 실행하세요.

set -e

PROJECT_ROOT="/opt/sales-portal"

echo "========================================"
echo "⚠️  운영 서버 완전 삭제 스크립트"
echo "========================================"
echo ""
echo "이 스크립트는 다음을 완전히 삭제합니다:"
echo "  1. 프로젝트 디렉토리: $PROJECT_ROOT"
echo "  2. 모든 백업 파일: $PROJECT_ROOT/db_dumps"
echo "  3. 모든 로그 파일: $PROJECT_ROOT/logs"
echo "  4. 실행 중인 프로세스 (Backend/Frontend)"
echo "  5. 모든 스크립트 파일 (.sh, .ps1)"
echo "  6. 데이터베이스 데이터 (선택사항)"
echo ""
echo "⚠️  이 작업은 되돌릴 수 없습니다!"
echo ""

# 1차 확인
read -p "정말로 운영 서버의 모든 데이터를 삭제하시겠습니까? (yes/no): " CONFIRM1
if [ "$CONFIRM1" != "yes" ]; then
    echo "작업이 취소되었습니다."
    exit 0
fi

# 2차 확인
echo ""
echo "⚠️  마지막 확인: 'DELETE ALL'을 입력하세요"
read -p "입력: " CONFIRM2
if [ "$CONFIRM2" != "DELETE ALL" ]; then
    echo "작업이 취소되었습니다."
    exit 0
fi

echo ""
echo "========================================"
echo "서버 삭제 시작..."
echo "========================================"
echo ""

echo "[1/6] 실행 중인 프로세스 확인 및 중지..."

# Backend 프로세스 중지
if pgrep -f "python.*manage.py runserver" > /dev/null; then
    echo "  Backend 프로세스 중지 중..."
    pkill -f "python.*manage.py runserver" || true
    sleep 2
fi

# Frontend 프로세스 중지
if pgrep -f "node.*next" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
    echo "  Frontend 프로세스 중지 중..."
    pkill -f "node.*next" || true
    pkill -f "npm.*start" || true
    sleep 2
fi

echo "✅ 프로세스 중지 완료"
echo ""

echo "[2/6] Cron 작업 제거..."
# Django crontab 제거
if [ -d "$PROJECT_ROOT/backend" ]; then
    cd "$PROJECT_ROOT/backend"
    if [ -d "venv" ]; then
        source venv/bin/activate 2>/dev/null || true
        python manage.py crontab remove 2>/dev/null || true
    fi
fi
echo "✅ Cron 작업 제거 완료"
echo ""

echo "[3/6] 프로젝트 디렉토리 삭제..."
if [ -d "$PROJECT_ROOT" ]; then
    echo "  삭제 중: $PROJECT_ROOT"
    # root 권한이 필요한 경우
    if [ -w "$(dirname "$PROJECT_ROOT")" ]; then
        rm -rf "$PROJECT_ROOT"
    else
        echo "  root 권한이 필요합니다. 비밀번호를 입력하세요:"
        sudo rm -rf "$PROJECT_ROOT"
    fi
    echo "✅ 프로젝트 디렉토리 삭제 완료"
else
    echo "⚠️  프로젝트 디렉토리가 없습니다: $PROJECT_ROOT"
fi
echo ""

echo "[4/6] 로그 디렉토리 확인 및 삭제..."
if [ -d "/opt/sales-portal/logs" ]; then
    echo "  삭제 중: /opt/sales-portal/logs"
    if [ -w "/opt" ]; then
        rm -rf /opt/sales-portal/logs
    else
        sudo rm -rf /opt/sales-portal/logs
    fi
    echo "✅ 로그 디렉토리 삭제 완료"
fi
echo ""

echo "[5/6] 백업 디렉토리 확인 및 삭제..."
if [ -d "/opt/sales-portal/db_dumps" ]; then
    echo "  삭제 중: /opt/sales-portal/db_dumps"
    if [ -w "/opt" ]; then
        rm -rf /opt/sales-portal/db_dumps
    else
        sudo rm -rf /opt/sales-portal/db_dumps
    fi
    echo "✅ 백업 디렉토리 삭제 완료"
fi
echo ""

echo "[6/6] 남은 파일 확인..."
# 혹시 남은 파일이 있는지 확인
if [ -d "/opt/sales-portal" ]; then
    echo "⚠️  남은 파일이 있습니다:"
    ls -la /opt/sales-portal/ 2>/dev/null || true
    echo "  강제 삭제 중..."
    if [ -w "/opt" ]; then
        rm -rf /opt/sales-portal
    else
        sudo rm -rf /opt/sales-portal
    fi
fi

# 프로세스 재확인
if pgrep -f "sales-portal" > /dev/null; then
    echo "⚠️  남은 프로세스가 있습니다. 강제 종료 중..."
    pkill -9 -f "sales-portal" || true
fi

echo ""
echo "========================================"
echo "✅ 서버 파일 삭제 완료"
echo "========================================"
echo ""

read -p "데이터베이스 데이터도 삭제하시겠습니까? (yes/no): " DELETE_DB
if [ "$DELETE_DB" = "yes" ]; then
    echo ""
    echo "데이터베이스 삭제를 진행합니다..."
    
    export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
    export PATH=$ORACLE_HOME/bin:$PATH
    export ORACLE_SID=XEPDB1
    
    sqlplus -s salesportal/salesportal123 <<SQL
SET PAGESIZE 0
SET FEEDBACK OFF
SET HEADING OFF
SET ECHO OFF

BEGIN
  FOR cur_rec IN (SELECT object_name, object_type FROM user_objects WHERE object_type = 'TABLE') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP TABLE ' || cur_rec.object_name || ' CASCADE CONSTRAINTS';
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

BEGIN
  FOR cur_rec IN (SELECT object_name FROM user_objects WHERE object_type = 'SEQUENCE') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP SEQUENCE ' || cur_rec.object_name;
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

BEGIN
  FOR cur_rec IN (SELECT object_name FROM user_objects WHERE object_type = 'VIEW') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP VIEW ' || cur_rec.object_name;
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

EXIT;
SQL

    echo "✅ 데이터베이스 데이터 삭제 완료"
fi

echo ""
echo "========================================"
echo "✅ 모든 삭제 작업 완료!"
echo "========================================"

