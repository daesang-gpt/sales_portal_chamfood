#!/bin/bash

# 서버에 직접 wipe_production_server.sh 파일을 생성하는 스크립트

SERVER_IP="192.168.99.37"
SERVER_USER="adm1003701"
REMOTE_PATH="/opt/sales-portal"

echo "========================================"
echo "서버에 삭제 스크립트 생성"
echo "========================================"
echo ""

# 로컬 파일 읽기
if [ ! -f "wipe_production_server.sh" ]; then
    echo "❌ 오류: wipe_production_server.sh 파일을 찾을 수 없습니다."
    exit 1
fi

echo "[1/2] 서버에 스크립트 생성 중..."

# SSH로 파일 내용을 전송하여 서버에 생성
cat wipe_production_server.sh | ssh "${SERVER_USER}@${SERVER_IP}" "cat > ${REMOTE_PATH}/wipe_production_server.sh"

if [ $? -eq 0 ]; then
    echo "✅ 스크립트 생성 완료!"
    echo ""
    
    echo "[2/2] 실행 권한 부여 중..."
    ssh "${SERVER_USER}@${SERVER_IP}" "chmod +x ${REMOTE_PATH}/wipe_production_server.sh"
    
    if [ $? -eq 0 ]; then
        echo "✅ 실행 권한 부여 완료!"
        echo ""
        echo "========================================"
        echo "✅ 완료!"
        echo "========================================"
        echo ""
        echo "서버에서 실행 방법:"
        echo "  ssh ${SERVER_USER}@${SERVER_IP}"
        echo "  cd ${REMOTE_PATH}"
        echo "  ./wipe_production_server.sh"
    else
        echo "❌ 실행 권한 부여 실패"
    fi
else
    echo "❌ 스크립트 생성 실패"
fi

