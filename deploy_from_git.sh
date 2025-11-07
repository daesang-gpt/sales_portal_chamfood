#!/bin/bash

# Git을 통한 운영서버 배포 스크립트

echo "=== Git 기반 배포 시작 ==="

# 배포 설정
REPO_URL="https://github.com/your-username/sales-portal.git"  # 실제 Git 저장소 URL로 변경
DEPLOY_DIR="/opt/sales-portal"
BACKUP_DIR="/opt/sales-portal-backup-$(date +%Y%m%d_%H%M%S)"

# 원격 서버 강제 pull 설정 (필요 시 환경변수로 덮어쓰기 가능)
REMOTE_HOST=${REMOTE_HOST:-"192.168.99.37"}
REMOTE_USER=${REMOTE_USER:-"adm1003701"}
REMOTE_PROJECT_DIR=${REMOTE_PROJECT_DIR:-"/opt/sales-portal"}
FORCE_REMOTE_PULL=${FORCE_REMOTE_PULL:-"true"}

if [ "$FORCE_REMOTE_PULL" = "true" ]; then
    echo "🌐 원격 운영서버에서 git pull (강제) 실행 중..."
    ssh "${REMOTE_USER}@${REMOTE_HOST}" bash <<EOF
set -e
cd "${REMOTE_PROJECT_DIR}"
if [ -d .git ]; then
    sudo git fetch --all
    sudo git reset --hard origin/main
else
    sudo git clone "${REPO_URL}" "${REMOTE_PROJECT_DIR}"
fi
EOF
    echo "✅ 원격 강제 pull 완료"
fi

# 1. 기존 배포 백업
if [ -d "$DEPLOY_DIR" ]; then
    echo "기존 배포 백업 중..."
    sudo cp -r $DEPLOY_DIR $BACKUP_DIR
fi

# 2. Git에서 최신 코드 가져오기
echo "Git에서 최신 코드 가져오는 중..."
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd $DEPLOY_DIR
    sudo git pull origin main
else
    sudo rm -rf $DEPLOY_DIR
    sudo git clone $REPO_URL $DEPLOY_DIR
fi

# 3. 권한 설정
sudo chown -R adm1003701:adm1003701 $DEPLOY_DIR

# 4. Backend 설정
echo "Backend 환경 설정 중..."
cd $DEPLOY_DIR/backend

# Python 가상환경 생성/업데이트
if [ ! -d "venv" ]; then
    python3.9 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Frontend 설정
echo "Frontend 환경 설정 중..."
cd $DEPLOY_DIR/frontend
npm install
npm run build

# 6. Database 마이그레이션
echo "Database 마이그레이션 실행 중..."
cd $DEPLOY_DIR/backend
source venv/bin/activate

# 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

python manage.py migrate

echo "=== 배포 완료 ==="
echo "Backend: http://192.168.99.37:8000"
echo "Frontend: http://192.168.99.37:3000"
