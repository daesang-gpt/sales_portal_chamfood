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

# 1. 로그 파일 로테이션 (30일 이상 된 로그 삭제)
echo "[1/6] 오래된 로그 파일 정리 중..."
if [ -d "$PROJECT_ROOT/logs" ]; then
    find "$PROJECT_ROOT/logs" -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true
    echo "✅ 로그 파일 정리 완료"
else
    echo "⚠️  로그 디렉토리가 없습니다: $PROJECT_ROOT/logs"
fi

# 2. 만료된 세션 데이터 정리
echo "[2/6] 만료된 세션 데이터 정리 중..."
python manage.py clearsessions 2>/dev/null || {
    echo "⚠️  세션 정리 실패 (정상일 수 있음)"
}
echo "✅ 세션 데이터 정리 완료"

# 3. JWT 토큰 블랙리스트 정리 (만료된 토큰)
echo "[3/6] 만료된 JWT 토큰 정리 중..."
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
echo "[4/6] 정적 파일 수집 중..."
python manage.py collectstatic --noinput --clear 2>/dev/null || {
    echo "⚠️  정적 파일 수집 실패 (정상일 수 있음)"
}
echo "✅ 정적 파일 수집 완료"

# 5. 데이터베이스 통계 업데이트 (Oracle 성능 최적화)
echo "[5/6] 데이터베이스 통계 업데이트 중..."
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
echo "[6/6] 디스크 공간 확인 중..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️  경고: 디스크 사용량이 ${DISK_USAGE}%입니다!"
    echo "   오래된 백업 파일이나 로그를 정리하세요."
else
    echo "✅ 디스크 사용량: ${DISK_USAGE}% (정상)"
fi

echo ""
echo "========================================"
echo "✅ 모든 배치 작업 완료: $(date)"
echo "========================================"

