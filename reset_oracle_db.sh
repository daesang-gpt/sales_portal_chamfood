#!/bin/bash
# Oracle DB 초기화 스크립트 (모든 테이블 및 데이터 삭제)
# 사용법: ./reset_oracle_db.sh

set -e

echo "========================================"
echo "Oracle DB 초기화 시작"
echo "========================================"
echo "⚠️  경고: 모든 테이블과 데이터가 삭제됩니다!"
echo ""

# 확인
read -p "정말로 모든 데이터를 삭제하시겠습니까? (yes 입력): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "취소되었습니다."
    exit 1
fi

cd /opt/sales-portal/backend
source venv/bin/activate

# 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

echo ""
echo "[1/3] 모든 테이블 삭제 중..."
python3 << 'PYTHON_SCRIPT'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.production')
django.setup()

from django.db import connection

cursor = connection.cursor()

# Foreign Key 제약조건 비활성화
print("Foreign Key 제약조건 비활성화 중...")
try:
    cursor.execute("""
        BEGIN
            FOR r IN (SELECT constraint_name, table_name 
                     FROM user_constraints 
                     WHERE constraint_type = 'R') LOOP
                EXECUTE IMMEDIATE 'ALTER TABLE ' || r.table_name || 
                                 ' DROP CONSTRAINT ' || r.constraint_name;
            END LOOP;
        END;
    """)
    print("✅ Foreign Key 제약조건 삭제 완료")
except Exception as e:
    print(f"⚠️  Foreign Key 제약조건 삭제 중 오류 (무시 가능): {e}")

# 모든 테이블 삭제
print("모든 테이블 삭제 중...")
try:
    cursor.execute("""
        BEGIN
            FOR r IN (SELECT table_name FROM user_tables) LOOP
                BEGIN
                    EXECUTE IMMEDIATE 'DROP TABLE ' || r.table_name || ' CASCADE CONSTRAINTS PURGE';
                EXCEPTION
                    WHEN OTHERS THEN
                        NULL;
                END;
            END LOOP;
        END;
    """)
    print("✅ 모든 테이블 삭제 완료")
except Exception as e:
    print(f"⚠️  테이블 삭제 중 오류: {e}")

# 모든 시퀀스 삭제
print("모든 시퀀스 삭제 중...")
try:
    cursor.execute("""
        BEGIN
            FOR r IN (SELECT sequence_name FROM user_sequences) LOOP
                BEGIN
                    EXECUTE IMMEDIATE 'DROP SEQUENCE ' || r.sequence_name;
                EXCEPTION
                    WHEN OTHERS THEN
                        NULL;
                END;
            END LOOP;
        END;
    """)
    print("✅ 모든 시퀀스 삭제 완료")
except Exception as e:
    print(f"⚠️  시퀀스 삭제 중 오류 (무시 가능): {e}")

# Django 마이그레이션 테이블도 삭제 (있으면)
try:
    cursor.execute("DROP TABLE django_migrations CASCADE CONSTRAINTS PURGE")
    print("✅ Django 마이그레이션 테이블 삭제 완료")
except Exception as e:
    print(f"⚠️  Django 마이그레이션 테이블 삭제 중 오류 (무시 가능): {e}")

connection.close()
print("✅ DB 초기화 완료")
PYTHON_SCRIPT

echo ""
echo "[2/3] 마이그레이션 파일 백업 및 초기화..."
# 기존 마이그레이션 파일 백업 (필요시 참고용)
if [ -d "myapi/migrations" ]; then
    MIGRATIONS_BACKUP="myapi/migrations_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$MIGRATIONS_BACKUP"
    cp -r myapi/migrations/* "$MIGRATIONS_BACKUP/" 2>/dev/null || true
    echo "기존 마이그레이션 파일 백업: $MIGRATIONS_BACKUP"
    
    # 마이그레이션 파일 삭제 (__init__.py 제외)
    find myapi/migrations -name "*.py" ! -name "__init__.py" -delete 2>/dev/null || true
    find myapi/migrations -name "*.pyc" -delete 2>/dev/null || true
    find myapi/migrations -name "__pycache__" -type d -exec rm -r {} + 2>/dev/null || true
    echo "✅ 기존 마이그레이션 파일 삭제 완료"
fi

echo ""
echo "[3/3] 마이그레이션 재생성 및 적용 중..."
# 현재 모델 상태로 새 마이그레이션 생성
echo "새 마이그레이션 파일 생성 중..."
python manage.py makemigrations myapi

# 마이그레이션 적용 (초기 마이그레이션으로 표시)
echo "마이그레이션 적용 중..."
python manage.py migrate --run-syncdb

echo ""
echo "========================================"
echo "✅ DB 초기화 완료!"
echo "========================================"
echo ""
echo "다음 단계:"
echo "  1. 개발 DB에서 덤프 생성: export_db.bat (Windows)"
echo "  2. 덤프 파일을 운영서버로 복사"
echo "  3. 데이터 복원: ./import_db.sh <덤프파일>"

