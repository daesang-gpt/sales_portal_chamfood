#!/bin/bash

# 서버 정리 스크립트 - 불필요한 파일들 삭제

echo "=== 서버 정리 시작 ==="

DEPLOY_DIR="/opt/sales-portal"

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "배포 디렉토리가 존재하지 않습니다: $DEPLOY_DIR"
    exit 1
fi

cd $DEPLOY_DIR

echo "1. Python 캐시 파일 삭제 중..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

echo "2. Node.js 캐시 및 빌드 파일 정리 중..."
if [ -d "frontend/node_modules" ]; then
    echo "   - node_modules 크기 확인 중..."
    du -sh frontend/node_modules
fi

if [ -d "frontend/.next" ]; then
    echo "   - Next.js 캐시 정리 중..."
    rm -rf frontend/.next/.cache
fi

echo "3. 로그 파일 정리 중..."
find . -name "*.log" -type f -mtime +7 -delete
find . -name "*.log.*" -type f -mtime +7 -delete

echo "4. 임시 파일 삭제 중..."
find . -name "*.tmp" -delete
find . -name "*.temp" -delete
find . -name "*~" -delete

echo "5. Git 관련 파일 정리 중..."
if [ -d ".git" ]; then
    cd .git
    git gc --prune=now
    cd ..
fi

echo "6. 개발 도구 파일 삭제 중..."
rm -rf .vscode
rm -rf .idea

echo "7. 환경 파일 확인 중..."
if [ -f ".env" ]; then
    echo "   - .env 파일이 존재합니다. 보안상 확인이 필요합니다."
fi

echo "8. 디스크 사용량 확인..."
echo "정리 후 디렉토리 크기:"
du -sh $DEPLOY_DIR

echo "9. 권한 재설정..."
sudo chown -R adm1003701:adm1003701 $DEPLOY_DIR

echo "=== 서버 정리 완료 ==="

# 선택적 정리 (주석 해제하여 사용)
echo ""
echo "추가 정리 옵션 (수동 실행):"
echo "- 오래된 백업 삭제: find /opt -name 'sales-portal-backup-*' -mtime +30 -exec rm -rf {} +"
echo "- node_modules 재설치: rm -rf frontend/node_modules && npm install"
echo "- Python 가상환경 재생성: rm -rf backend/venv && python3.9 -m venv backend/venv"
