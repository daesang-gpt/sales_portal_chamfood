#!/bin/bash

# 운영 DB 백업 스크립트
# 사용법: ./backup_db.sh
# cron 설정 예시: 0 4 * * * /opt/sales-portal/backup_db.sh >> /opt/sales-portal/logs/backup.log 2>&1

set -e

PROJECT_ROOT="/opt/sales-portal"
BACKUP_DIR="$PROJECT_ROOT/db_dumps"

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

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
echo "데이터베이스 백업 시작: $(date)"
echo "========================================"

# 디스크 공간 확인 (GB 단위, 루트 파티션)
AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')

if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    echo "❌ 디스크 공간 부족 (사용 가능: ${AVAILABLE_SPACE}GB). 백업을 건너뜁니다."
    exit 1
fi

echo "사용 가능한 디스크 공간: ${AVAILABLE_SPACE}GB"

# 오래된 백업 파일 정리 (30일 이상)
echo ""
echo "[1/3] 오래된 백업 파일 정리 중 (30일 이상)..."
if [ -d "$BACKUP_DIR" ]; then
    OLD_BACKUPS=$(find "$BACKUP_DIR" -name "db_dump_*.json" -type f -mtime +30 2>/dev/null | wc -l)
    if [ "$OLD_BACKUPS" -gt 0 ]; then
        find "$BACKUP_DIR" -name "db_dump_*.json" -type f -mtime +30 -delete 2>/dev/null || true
        echo "✅ ${OLD_BACKUPS}개의 오래된 백업 파일 삭제 완료"
    else
        echo "✅ 삭제할 오래된 백업 파일이 없습니다"
    fi
else
    echo "⚠️  백업 디렉토리가 없습니다. 생성합니다."
    mkdir -p "$BACKUP_DIR"
fi

# 데이터베이스 백업 실행
echo ""
echo "[2/3] 데이터베이스 백업 실행 중..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_dump_${TIMESTAMP}.json"

# dump_db_utf8.py 스크립트 사용 (UTF-8 인코딩 처리)
if [ -f "$PROJECT_ROOT/backend/dump_db_utf8.py" ]; then
    # 운영 환경 설정으로 변경
    python <<PYTHON_SCRIPT
import os
import sys
import django

# 운영 환경 설정
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.production'
os.environ['DB_NAME'] = '192.168.99.37:1521/XEPDB1'
os.environ['DB_USER'] = 'salesportal'
os.environ['DB_PASSWORD'] = 'salesportal123'

# Oracle 환경변수
os.environ['ORACLE_HOME'] = '/u01/app/oracle/product/19c/db_1'
os.environ['LD_LIBRARY_PATH'] = f"{os.environ['ORACLE_HOME']}/lib"
os.environ['PATH'] = f"{os.environ['ORACLE_HOME']}/bin:{os.environ['PATH']}"

# 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Django 설정
sys.path.insert(0, '$PROJECT_ROOT/backend')
django.setup()

# dump_db_utf8.py의 로직 실행
import json
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from datetime import datetime

def dump_model(model_name, output_file):
    try:
        output = StringIO()
        call_command('dumpdata', model_name, indent=2, stdout=output, skip_checks=True)
        data = output.getvalue()
        
        if data.strip():
            json_data = json.loads(data)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✅ {model_name} 덤프 완료")
            return True
        else:
            print(f"⚠️ {model_name} 데이터가 없습니다.")
            return False
    except Exception as e:
        print(f"❌ {model_name} 덤프 실패: {e}")
        return False

def merge_json_files(files, output_file):
    all_data = []
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
        except Exception as e:
            print(f"⚠️ 파일 병합 실패 ({file_path}): {e}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 병합 완료: {output_file}")

# 각 모델을 개별적으로 덤프
models = [
    'myapi.User',
    'myapi.Company',
    'myapi.Report',
    'myapi.CompanyFinancialStatus',
    'myapi.SalesData'
]

import tempfile
import shutil
temp_dir = tempfile.mkdtemp()
temp_files = []

# 타임스탬프 생성 (Python에서)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = '$BACKUP_FILE'

for model in models:
    temp_file = os.path.join(temp_dir, f'temp_{model.replace(".", "_")}_{timestamp}.json')
    if dump_model(model, temp_file):
        temp_files.append(temp_file)

# 모든 파일을 하나로 병합
if temp_files:
    merge_json_files(temp_files, backup_file)
    
    # 임시 파일 삭제
    shutil.rmtree(temp_dir)
    
    print(f"\\n✅ 전체 덤프 완료: {backup_file}")
else:
    print("\\n❌ 덤프할 데이터가 없습니다.")
    shutil.rmtree(temp_dir)
    sys.exit(1)
PYTHON_SCRIPT

    if [ $? -eq 0 ] && [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "✅ 백업 완료: $BACKUP_FILE (크기: $BACKUP_SIZE)"
    else
        echo "❌ 백업 실패"
        exit 1
    fi
else
    echo "❌ dump_db_utf8.py 파일을 찾을 수 없습니다: $PROJECT_ROOT/backend/dump_db_utf8.py"
    exit 1
fi

# 백업 파일 압축 (선택사항)
echo ""
echo "[3/3] 백업 파일 압축 중..."
if command -v gzip >/dev/null 2>&1; then
    gzip -f "$BACKUP_FILE"
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
    echo "✅ 압축 완료: $COMPRESSED_FILE (크기: $COMPRESSED_SIZE)"
else
    echo "⚠️  gzip이 설치되지 않아 압축을 건너뜁니다."
fi

echo ""
echo "========================================"
echo "✅ 데이터베이스 백업 완료: $(date)"
echo "========================================"

