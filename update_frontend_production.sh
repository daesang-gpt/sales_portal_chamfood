#!/bin/bash

# 운영서버 프론트엔드만 업데이트하는 스크립트
# 사용법: ./update_frontend_production.sh

set -e

PROJECT_DIR=${PROJECT_DIR:-"/opt/sales-portal"}
cd "$PROJECT_DIR/frontend"

echo "🔄 프론트엔드 업데이트를 시작합니다..."

# 1. 최신 코드 가져오기
echo "📥 최신 코드를 가져옵니다..."
cd "$PROJECT_DIR"
git pull origin main

# 2. Next.js 빌드 캐시 삭제
echo "🧹 Next.js 빌드 캐시 삭제 중..."
cd "$PROJECT_DIR/frontend"
rm -rf .next
rm -rf node_modules/.cache

# 3. 의존성 설치
echo "📦 프론트엔드 의존성을 설치합니다..."
npm install

# 4. 프로덕션 빌드
echo "🏗️ 프론트엔드를 빌드합니다..."
npm run build

# 5. 프론트엔드 서비스 재시작
echo "🔄 프론트엔드 서비스를 재시작합니다..."

# systemd 서비스 사용 시
if systemctl is-active --quiet sales-portal-frontend 2>/dev/null; then
    sudo systemctl restart sales-portal-frontend
    echo "✅ systemd 서비스로 재시작되었습니다."
# daemon 스크립트 사용 시
elif [ -f "$PROJECT_DIR/stop_frontend.sh" ] && [ -f "$PROJECT_DIR/start_frontend_daemon.sh" ]; then
    echo "프론트엔드 프로세스 중지 중..."
    "$PROJECT_DIR/stop_frontend.sh" || true
    sleep 2
    echo "프론트엔드 프로세스 시작 중..."
    "$PROJECT_DIR/start_frontend_daemon.sh"
    echo "✅ daemon 스크립트로 재시작되었습니다."
# 직접 프로세스 관리 시
elif pgrep -f "next start" > /dev/null; then
    echo "기존 프론트엔드 프로세스 종료 중..."
    pkill -f "next start" || true
    sleep 2
    echo "프론트엔드 프로세스 시작 중..."
    cd "$PROJECT_DIR"
    ./start_frontend_daemon.sh
    echo "✅ 프로세스로 재시작되었습니다."
else
    echo "⚠️  실행 중인 프론트엔드 프로세스를 찾을 수 없습니다."
    echo "수동으로 시작해주세요: cd $PROJECT_DIR && ./start_frontend_daemon.sh"
fi

# 6. 상태 확인
echo ""
echo "📊 프론트엔드 상태 확인 중..."
sleep 3

if systemctl is-active --quiet sales-portal-frontend 2>/dev/null; then
    sudo systemctl status sales-portal-frontend --no-pager | head -n 10
elif pgrep -f "next start" > /dev/null; then
    echo "✅ 프론트엔드가 실행 중입니다."
    ps aux | grep "next start" | grep -v grep | head -n 3
else
    echo "⚠️  프론트엔드가 실행 중이지 않습니다."
fi

echo ""
echo "✅ 프론트엔드 업데이트가 완료되었습니다!"
echo "🌐 접속 주소: http://192.168.99.37:3000"

