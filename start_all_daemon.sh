#!/bin/bash

# 백엔드와 프론트엔드를 모두 백그라운드에서 시작하는 스크립트

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT"

echo "========================================"
echo "백엔드 및 프론트엔드 시작"
echo "========================================"
echo ""

# Backend 시작
echo "[1/2] Backend 시작 중..."
./start_backend_daemon.sh
if [ $? -ne 0 ]; then
    echo "⚠️  Backend 시작 실패"
    exit 1
fi

echo ""
sleep 2

# Frontend 시작
echo "[2/2] Frontend 시작 중..."
./start_frontend_daemon.sh
if [ $? -ne 0 ]; then
    echo "⚠️  Frontend 시작 실패"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ 모든 서버가 시작되었습니다!"
echo "========================================"
echo ""
echo "상태 확인: ./status.sh"
echo "Backend 로그: tail -f $PROJECT_ROOT/logs/backend.log"
echo "Frontend 로그: tail -f $PROJECT_ROOT/logs/frontend.log"
echo ""
echo "중지 방법:"
echo "  Backend만:  ./stop_backend.sh"
echo "  Frontend만: ./stop_frontend.sh"
echo "  모두 중지:  ./stop_all.sh"

