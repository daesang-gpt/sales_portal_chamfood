#!/bin/bash

# 운영 DB에 데이터 복원 스크립트
# 사용법: ./import_db.sh <덤프파일경로>

set -e  # 에러 발생시 스크립트 중단

if [ -z "$1" ]; then
    echo "사용법: ./import_db.sh <덤프파일경로>"
    echo "예시: ./import_db.sh db_dumps/db_dump_20250115_123456.json"
    exit 1
fi

DUMP_FILE=$1

# 절대 경로로 변환 (상대 경로인 경우)
if [[ ! "$DUMP_FILE" = /* ]]; then
    # 스크립트 위치 기준으로 절대 경로 생성
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    DUMP_FILE="$SCRIPT_DIR/$DUMP_FILE"
fi

if [ ! -f "$DUMP_FILE" ]; then
    echo "오류: 덤프 파일을 찾을 수 없습니다: $DUMP_FILE"
    exit 1
fi

echo "========================================"
echo "운영 DB 데이터 복원 시작"
echo "========================================"
echo "덤프 파일: $DUMP_FILE"
echo ""

# 프로젝트 루트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT/backend"

# Python 가상환경 활성화
if [ ! -d "venv" ]; then
    echo "오류: 가상환경을 찾을 수 없습니다."
    exit 1
fi

source venv/bin/activate

# Oracle 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

# Django 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# 운영 DB 백업 확인
echo "⚠️  경고: 운영 DB의 기존 데이터가 덮어씌워질 수 있습니다."
echo "계속하시겠습니까? (yes/no)"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "복원이 취소되었습니다."
    exit 0
fi

# DB 연결 테스트
echo ""
echo "DB 연결 테스트 중..."
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('✅ DB 연결 성공!')" || {
    echo "❌ DB 연결 실패"
    exit 1
}

# 기존 데이터 삭제 (선택사항)
echo ""
echo "기존 데이터를 삭제하시겠습니까? (yes/no)"
echo "주의: 모든 사용자, 회사, 보고서 데이터가 삭제됩니다!"
read -r DELETE_CONFIRM

if [ "$DELETE_CONFIRM" = "yes" ]; then
    echo "기존 데이터 삭제 중..."
    python manage.py shell <<EOF
from myapi.models import User, Company, Report, CompanyFinancialStatus, SalesData
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

# 외래키 제약조건 때문에 순서 중요
SalesData.objects.all().delete()
CompanyFinancialStatus.objects.all().delete()
Report.objects.all().delete()
Company.objects.all().delete()
User.objects.all().delete()

print("✅ 기존 데이터 삭제 완료")
EOF
fi

# 데이터 복원
echo ""
echo "데이터 복원 중..."
cd "$PROJECT_ROOT"
python manage.py loaddata "$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ 데이터 복원 완료!"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "❌ 오류: 데이터 복원 실패"
    echo "========================================"
    exit 1
fi

