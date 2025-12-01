#!/bin/bash

# 운영 서버 DB 다운로드 스크립트 (Bash 버전)
# 사용법: 
#   ./download_production_db.sh [--skip-backup]
#   ./download_production_db.sh --file db_dump_20251201_103420.json.gz

set -e  # 에러 발생시 스크립트 중단

# 옵션 파싱
SKIP_BACKUP=false
FILE_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup|-s)
            SKIP_BACKUP=true
            shift
            ;;
        --file|-f)
            FILE_NAME="$2"
            shift 2
            ;;
        *)
            echo "알 수 없는 옵션: $1" >&2
            echo "사용법: ./download_production_db.sh [--skip-backup] [--file 파일명]" >&2
            exit 1
            ;;
    esac
done

echo "========================================"
echo "운영 서버 DB 다운로드 시작"
echo "========================================"
echo ""

# 서버 정보
SERVER_IP="192.168.99.37"
SERVER_USER="adm1003701"
PROJECT_PATH="/opt/sales-portal"
BACKUP_DIR="$PROJECT_PATH/db_dumps"

# 로컬 다운로드 디렉토리
LOCAL_DOWNLOAD_DIR="./db_dumps"
mkdir -p "$LOCAL_DOWNLOAD_DIR"
echo "✅ 로컬 다운로드 디렉토리: $LOCAL_DOWNLOAD_DIR"

backup_file=""

# 특정 파일명이 지정된 경우
if [ -n "$FILE_NAME" ]; then
    backup_file="$BACKUP_DIR/$FILE_NAME"
    echo ""
    echo "[1/4] 지정된 파일 다운로드: $FILE_NAME"
    
    # 파일 존재 확인
    if ssh "${SERVER_USER}@${SERVER_IP}" "test -f \"$backup_file\"" 2>/dev/null; then
        echo "✅ 파일 확인 완료: $backup_file"
        echo ""
    else
        echo "❌ 지정된 파일을 찾을 수 없습니다: $backup_file" >&2
        echo "서버의 백업 파일 목록:" >&2
        ssh "${SERVER_USER}@${SERVER_IP}" "ls -lh $BACKUP_DIR/" 2>&1
        exit 1
    fi
elif [ "$SKIP_BACKUP" = false ]; then
    echo ""
    echo "[1/4] 운영 서버에서 DB 백업 실행 중..."
    
    # SSH로 서버에 접속하여 백업 실행
    ssh_result=$(ssh "${SERVER_USER}@${SERVER_IP}" <<'ENDSSH'
cd /opt/sales-portal
if [ ! -f backup_db.sh ]; then
    echo "❌ backup_db.sh 파일을 찾을 수 없습니다: /opt/sales-portal/backup_db.sh" >&2
    exit 1
fi

chmod +x backup_db.sh
echo "========================================"
echo "운영 DB 백업 실행 중..."
echo "========================================"
./backup_db.sh

if [ $? -eq 0 ]; then
    echo "✅ 백업 완료"
    # 가장 최근 백업 파일 찾기 (압축 파일 우선, 없으면 JSON 파일)
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/db_dump_*.json.gz 2>/dev/null | head -1)
    if [ -z "$LATEST_BACKUP" ]; then
        LATEST_BACKUP=$(ls -t $BACKUP_DIR/db_dump_*.json 2>/dev/null | head -1)
    fi
    if [ -n "$LATEST_BACKUP" ]; then
        echo "BACKUP_FILE:$LATEST_BACKUP"
    else
        echo "❌ 백업 파일을 찾을 수 없습니다." >&2
        exit 1
    fi
else
    echo "❌ 백업 실패" >&2
    exit 1
fi
ENDSSH
)
    
    if [ $? -ne 0 ]; then
        echo "❌ 백업 실행 실패" >&2
        echo "에러 메시지:" >&2
        echo "$ssh_result" >&2
        echo ""
        echo "참고: SSH 접속이 안 되는 경우 다음을 확인하세요:" >&2
        echo "  1. 서버 IP와 사용자명이 올바른지 확인" >&2
        echo "  2. SSH 키 또는 비밀번호 설정 확인" >&2
        echo "  3. 네트워크 연결 확인" >&2
        exit 1
    fi
    
    # 백업 파일 경로 추출
    while IFS= read -r line; do
        if [[ $line =~ BACKUP_FILE:(.+) ]]; then
            backup_file="${BASH_REMATCH[1]}"
            break
        fi
    done <<< "$ssh_result"
    
    if [ -z "$backup_file" ]; then
        echo "❌ 백업 파일 경로를 찾을 수 없습니다." >&2
        echo "백업 결과:" >&2
        echo "$ssh_result" >&2
        exit 1
    fi
    
    echo "✅ 백업 파일 생성 완료: $backup_file"
    echo ""
else
    echo "[1/4] 기존 백업 파일 찾기 중..."
    
    # 서버에서 가장 최근 백업 파일 찾기
    find_result=$(ssh "${SERVER_USER}@${SERVER_IP}" <<'ENDSSH'
LATEST_BACKUP=$(ls -t /opt/sales-portal/db_dumps/db_dump_*.json.gz 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    LATEST_BACKUP=$(ls -t /opt/sales-portal/db_dumps/db_dump_*.json 2>/dev/null | head -1)
fi
if [ -n "$LATEST_BACKUP" ]; then
    echo "BACKUP_FILE:$LATEST_BACKUP"
else
    echo "❌ 백업 파일을 찾을 수 없습니다." >&2
    exit 1
fi
ENDSSH
)
    
    if [ $? -ne 0 ]; then
        echo "❌ 백업 파일 찾기 실패" >&2
        echo "$find_result" >&2
        exit 1
    fi
    
    while IFS= read -r line; do
        if [[ $line =~ BACKUP_FILE:(.+) ]]; then
            backup_file="${BASH_REMATCH[1]}"
            break
        fi
    done <<< "$find_result"
    
    if [ -z "$backup_file" ]; then
        echo "❌ 백업 파일을 찾을 수 없습니다." >&2
        exit 1
    fi
    
    echo "✅ 백업 파일 발견: $backup_file"
    echo ""
fi

# 파일명 추출
if [ -n "$FILE_NAME" ]; then
    file_name="$FILE_NAME"
else
    file_name=$(basename "$backup_file")
fi

echo "[2/4] 백업 파일 다운로드 중..."
echo "원본: ${SERVER_USER}@${SERVER_IP}:$backup_file"
echo "대상: $LOCAL_DOWNLOAD_DIR/$file_name"

# SCP로 파일 다운로드
scp "${SERVER_USER}@${SERVER_IP}:$backup_file" "$LOCAL_DOWNLOAD_DIR/$file_name"

if [ $? -ne 0 ]; then
    echo "❌ 파일 다운로드 실패" >&2
    echo "참고: SCP 접속이 안 되는 경우 다음을 확인하세요:" >&2
    echo "  1. SSH 키 또는 비밀번호 설정 확인" >&2
    echo "  2. 파일 경로와 권한 확인" >&2
    exit 1
fi

echo "✅ 파일 다운로드 완료: $LOCAL_DOWNLOAD_DIR/$file_name"

# 파일 크기 확인
if command -v stat >/dev/null 2>&1; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        file_size=$(stat -f%z "$LOCAL_DOWNLOAD_DIR/$file_name")
    else
        # Linux
        file_size=$(stat -c%s "$LOCAL_DOWNLOAD_DIR/$file_name")
    fi
    file_size_mb=$(echo "scale=2; $file_size / 1024 / 1024" | bc)
    echo "파일 크기: ${file_size_mb} MB"
else
    # stat이 없는 경우 ls 사용
    file_size_info=$(ls -lh "$LOCAL_DOWNLOAD_DIR/$file_name" | awk '{print $5}')
    echo "파일 크기: $file_size_info"
fi

# 압축 파일인 경우 압축 해제
if [[ "$file_name" =~ \.gz$ ]]; then
    echo ""
    echo "[3/4] 압축 해제 중..."
    uncompressed_file="${file_name%.gz}"
    
    if command -v gunzip >/dev/null 2>&1; then
        gunzip -c "$LOCAL_DOWNLOAD_DIR/$file_name" > "$LOCAL_DOWNLOAD_DIR/$uncompressed_file"
        if [ $? -eq 0 ]; then
            if command -v stat >/dev/null 2>&1; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    uncompressed_size=$(stat -f%z "$LOCAL_DOWNLOAD_DIR/$uncompressed_file")
                else
                    uncompressed_size=$(stat -c%s "$LOCAL_DOWNLOAD_DIR/$uncompressed_file")
                fi
                uncompressed_size_mb=$(echo "scale=2; $uncompressed_size / 1024 / 1024" | bc)
                echo "✅ 압축 해제 완료: $uncompressed_file (${uncompressed_size_mb} MB)"
            else
                uncompressed_size_info=$(ls -lh "$LOCAL_DOWNLOAD_DIR/$uncompressed_file" | awk '{print $5}')
                echo "✅ 압축 해제 완료: $uncompressed_file ($uncompressed_size_info)"
            fi
        else
            echo "❌ 압축 해제 실패" >&2
            exit 1
        fi
    else
        echo "❌ gunzip이 설치되지 않아 압축 해제를 할 수 없습니다." >&2
        echo "다음 명령으로 수동 압축 해제: gunzip $LOCAL_DOWNLOAD_DIR/$file_name" >&2
    fi
fi

echo ""
echo "========================================"
echo "✅ 운영 서버 DB 다운로드 완료!"
echo "========================================"
echo "다운로드 위치: $LOCAL_DOWNLOAD_DIR/$file_name"
if [[ "$file_name" =~ \.gz$ ]] && [ -f "$LOCAL_DOWNLOAD_DIR/${file_name%.gz}" ]; then
    echo "압축 해제 파일: $LOCAL_DOWNLOAD_DIR/${file_name%.gz}"
fi
echo ""

