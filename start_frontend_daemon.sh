#!/bin/bash

# 운영서버용 Next.js Frontend 백그라운드 실행 스크립트
# SSH 세션이 끊어져도 계속 실행됩니다

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT/frontend"

# 이미 실행 중인지 확인
if pgrep -f "next start" > /dev/null || pgrep -f "next-server" > /dev/null; then
    echo "⚠️  Frontend가 이미 실행 중입니다."
    echo "   중지하려면: ./stop_frontend.sh"
    exit 1
fi

# 프로덕션 빌드 확인
if [ ! -d ".next" ]; then
    echo "⚠️  프로덕션 빌드가 없습니다. 빌드를 시작합니다..."
    npm run build
    if [ $? -ne 0 ]; then
        echo "❌ 빌드 실패"
        exit 1
    fi
fi

# 로그 디렉토리 생성
mkdir -p "$PROJECT_ROOT/logs"

echo "========================================"
echo "Next.js Frontend 백그라운드 시작 중..."
echo "========================================"
echo "서버 주소: http://192.168.99.37:3000"
echo "로그 파일: $PROJECT_ROOT/logs/frontend.log"
echo ""

# 백그라운드에서 실행 (nohup 사용)
nohup npm start > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &

# 프로세스 ID 저장
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"

echo "✅ Frontend가 백그라운드에서 시작되었습니다."
echo "   PID: $FRONTEND_PID"
echo "   로그 확인: tail -f $PROJECT_ROOT/logs/frontend.log"
echo "   중지: ./stop_frontend.sh"
echo "   상태 확인: ./status.sh"
echo ""

# 잠시 대기 후 상태 확인
sleep 3
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend가 정상적으로 실행 중입니다."
else
    echo "⚠️  Frontend 시작에 실패했을 수 있습니다. 로그를 확인하세요:"
    echo "   tail -n 50 $PROJECT_ROOT/logs/frontend.log"
    exit 1
fi

