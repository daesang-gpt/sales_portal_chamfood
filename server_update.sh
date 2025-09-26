#!/bin/bash

# 운영서버에서 실행할 업데이트 스크립트
# 사용법: ./server_update.sh

set -e  # 에러 발생시 스크립트 중단

echo "🔄 서버 업데이트를 시작합니다..."

# 프로젝트 디렉토리로 이동
cd /var/www/sales-portal

# 1. 최신 코드 가져오기
echo "📥 최신 코드를 가져옵니다..."
git pull origin main

# 2. 백엔드 의존성 설치 및 마이그레이션
echo "🐍 백엔드 의존성을 설치합니다..."
cd backend
pip install -r requirements.txt

echo "🗄️ 데이터베이스 마이그레이션을 실행합니다..."
python manage.py migrate

# 3. 프론트엔드 의존성 설치 및 빌드
echo "📦 프론트엔드 의존성을 설치합니다..."
cd ../frontend
npm install

echo "🏗️ 프론트엔드를 빌드합니다..."
npm run build

# 4. 서비스 재시작
echo "🔄 서비스를 재시작합니다..."
sudo systemctl restart sales-portal-backend
sudo systemctl restart sales-portal-frontend

# 5. 서비스 상태 확인
echo "📊 서비스 상태를 확인합니다..."
sudo systemctl status sales-portal-backend --no-pager
sudo systemctl status sales-portal-frontend --no-pager

echo "✅ 서버 업데이트가 완료되었습니다!"
