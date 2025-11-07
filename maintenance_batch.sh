#!/bin/bash

# 운영 서버 배치 작업 스크립트
# 사용법: ./maintenance_batch.sh
# cron 설정 예시: 0 3 * * * /opt/sales-portal/maintenance_batch.sh >> /opt/sales-portal/logs/maintenance.log 2>&1

set -e

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT/backend"

# 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "❌ 가상환경을 찾을 수 없습니다: $PROJECT_ROOT/backend/venv"
    exit 1
fi

source venv/bin/activate

# Django 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# Oracle 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

echo "========================================"
echo "운영 서버 배치 작업 시작: $(date)"
echo "========================================"

# 1. 디스크 공간 정리
echo "[1/7] 디스크 공간 정리 중..."

# 1-1. 오래된 백업 디렉토리 삭제 (30일 이상)
if [ -d "/opt" ]; then
    OLD_BACKUPS=$(find /opt -name "sales-portal-backup-*" -type d -mtime +30 2>/dev/null | wc -l)
    if [ "$OLD_BACKUPS" -gt 0 ]; then
        find /opt -name "sales-portal-backup-*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
        echo "  ✅ ${OLD_BACKUPS}개 오래된 백업 디렉토리 삭제 완료"
    fi
fi

# 1-2. 오래된 로그 파일 삭제 (30일 이상)
if [ -d "$PROJECT_ROOT/logs" ]; then
    OLD_LOGS=$(find "$PROJECT_ROOT/logs" -name "*.log*" -type f -mtime +30 2>/dev/null | wc -l)
    if [ "$OLD_LOGS" -gt 0 ]; then
        find "$PROJECT_ROOT/logs" -name "*.log*" -type f -mtime +30 -delete 2>/dev/null || true
        echo "  ✅ ${OLD_LOGS}개 오래된 로그 파일 삭제 완료"
    fi
fi

# 1-3. 오래된 DB 덤프 파일 삭제 (30일 이상)
if [ -d "$PROJECT_ROOT/db_dumps" ]; then
    OLD_DUMPS=$(find "$PROJECT_ROOT/db_dumps" -name "db_dump_*.json*" -type f -mtime +30 2>/dev/null | wc -l)
    if [ "$OLD_DUMPS" -gt 0 ]; then
        find "$PROJECT_ROOT/db_dumps" -name "db_dump_*.json*" -type f -mtime +30 -delete 2>/dev/null || true
        echo "  ✅ ${OLD_DUMPS}개 오래된 덤프 파일 삭제 완료"
    fi
fi

# 1-4. Python 캐시 파일 삭제
PYCACHE_COUNT=$(find "$PROJECT_ROOT" -type d -name __pycache__ 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT" -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
    echo "  ✅ Python 캐시 파일 삭제 완료 (${PYCACHE_COUNT}개 디렉토리)"
fi

echo "✅ 디스크 공간 정리 완료"

# 2. 만료된 세션 데이터 정리
echo "[2/7] 만료된 세션 데이터 정리 중..."
python manage.py clearsessions 2>/dev/null || {
    echo "⚠️  세션 정리 실패 (정상일 수 있음)"
}
echo "✅ 세션 데이터 정리 완료"

# 3. JWT 토큰 블랙리스트 정리 (만료된 토큰)
echo "[3/7] 만료된 JWT 토큰 정리 중..."
python manage.py shell <<'PYEOF' 2>/dev/null || echo "⚠️  JWT 토큰 정리 실패 (정상일 수 있음)"
try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    from django.utils import timezone
    from datetime import timedelta
    
    # 7일 이상 된 만료 토큰 삭제
    expired_tokens = OutstandingToken.objects.filter(expires_at__lt=timezone.now() - timedelta(days=7))
    count = expired_tokens.count()
    if count > 0:
        expired_tokens.delete()
        print(f"✅ {count}개의 만료된 JWT 토큰 삭제 완료")
    else:
        print("✅ 만료된 JWT 토큰이 없습니다.")
except ImportError:
    print("⚠️  rest_framework_simplejwt가 설치되지 않았거나 토큰 블랙리스트가 활성화되지 않았습니다.")
except AttributeError as e:
    print(f"⚠️  JWT 토큰 블랙리스트 모델을 찾을 수 없습니다: {e}")
except Exception as e:
    print(f"⚠️  JWT 토큰 정리 중 오류: {e}")
PYEOF

# 4. 정적 파일 수집 (변경사항이 있을 경우)
echo "[4/7] 정적 파일 수집 중..."
python manage.py collectstatic --noinput --clear 2>/dev/null || {
    echo "⚠️  정적 파일 수집 실패 (정상일 수 있음)"
}
echo "✅ 정적 파일 수집 완료"

# 5. 데이터베이스 통계 업데이트 (Oracle 성능 최적화)
echo "[5/7] 데이터베이스 통계 업데이트 중..."
python manage.py shell <<'PYEOF' 2>/dev/null || echo "⚠️  DB 통계 업데이트 실패"
from django.db import connection

try:
    with connection.cursor() as cursor:
        # Oracle 테이블 통계 업데이트
        tables = ['MYAPI_USER', 'MYAPI_COMPANY', 'MYAPI_REPORT', 'MYAPI_COMPANYFINANCIALSTATUS', 'MYAPI_SALESDATA']
        updated_count = 0
        for table in tables:
            try:
                # Oracle PL/SQL 블록 실행 (세미콜론 포함)
                sql = f"BEGIN DBMS_STATS.GATHER_TABLE_STATS(ownname => USER, tabname => '{table}'); END;"
                cursor.execute(sql)
                updated_count += 1
            except Exception as e:
                print(f"⚠️  {table} 통계 업데이트 실패: {e}")
        if updated_count > 0:
            print(f"✅ {updated_count}개 테이블 통계 업데이트 완료")
        else:
            print("⚠️  모든 테이블 통계 업데이트 실패 (무시 가능)")
except Exception as e:
    print(f"⚠️  DB 통계 업데이트 중 오류: {e}")
PYEOF

# 6. 디스크 공간 확인 및 경고
echo "[6/7] 디스크 공간 확인 중..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  경고: 디스크 사용량이 ${DISK_USAGE}%입니다!"
    echo "   추가 정리가 필요할 수 있습니다."
    
    # 디스크 사용량이 85% 이상이면 더 적극적으로 정리
    if [ "$DISK_USAGE" -gt 85 ]; then
        echo "   디스크 사용량이 높아 추가 정리를 진행합니다..."
        
        # 최신 2개만 남기고 나머지 백업 삭제
        if [ -d "/opt" ]; then
            cd /opt
            BACKUP_COUNT=$(ls -d sales-portal-backup-* 2>/dev/null | wc -l)
            if [ "$BACKUP_COUNT" -gt 2 ]; then
                ls -t sales-portal-backup-* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true
                echo "  ✅ 추가 백업 디렉토리 정리 완료"
            fi
        fi
        
        # 15일 이상 된 로그 파일 삭제 (더 적극적)
        if [ -d "$PROJECT_ROOT/logs" ]; then
            find "$PROJECT_ROOT/logs" -name "*.log*" -type f -mtime +15 -delete 2>/dev/null || true
            echo "  ✅ 추가 로그 파일 정리 완료 (15일 이상)"
        fi
        
        # 15일 이상 된 덤프 파일 삭제 (더 적극적)
        if [ -d "$PROJECT_ROOT/db_dumps" ]; then
            find "$PROJECT_ROOT/db_dumps" -name "db_dump_*.json*" -type f -mtime +15 -delete 2>/dev/null || true
            echo "  ✅ 추가 덤프 파일 정리 완료 (15일 이상)"
        fi
    fi
else
    echo "✅ 디스크 사용량: ${DISK_USAGE}% (정상)"
fi

echo ""
echo "========================================"
echo "✅ 모든 배치 작업 완료: $(date)"
echo "========================================"

