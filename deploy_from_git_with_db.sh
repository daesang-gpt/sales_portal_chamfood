#!/bin/bash

# Git을 통한 운영서버 배포 스크립트 (코드 + DB 포함)
# 사용법: ./deploy_from_git_with_db.sh

set -e  # 에러 발생시 스크립트 중단

echo "========================================"
echo "Git 기반 배포 시작 (코드 + DB)"
echo "========================================"

# 배포 설정
REPO_URL="https://github.com/daesang-gpt/sales-portal.git"
DEPLOY_DIR="/opt/sales-portal"
BACKUP_DIR="/opt/sales-portal-backup-$(date +%Y%m%d_%H%M%S)"

# 1. 기존 배포 백업
if [ -d "$DEPLOY_DIR" ]; then
    echo ""
    echo "[1/7] 기존 배포 백업 중..."
    sudo cp -r $DEPLOY_DIR $BACKUP_DIR
    echo "백업 위치: $BACKUP_DIR"
fi

# 2. Git에서 최신 코드 가져오기
echo ""
echo "[2/7] Git에서 최신 코드 가져오는 중..."
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd $DEPLOY_DIR
    sudo git pull origin main
else
    sudo rm -rf $DEPLOY_DIR
    sudo git clone $REPO_URL $DEPLOY_DIR
fi

# 3. 권한 설정
echo ""
echo "[3/7] 권한 설정 중..."
sudo chown -R adm1003701:adm1003701 $DEPLOY_DIR

# 4. Backend 설정
echo ""
echo "[4/7] Backend 환경 설정 중..."
cd $DEPLOY_DIR/backend

# Python 가상환경 생성/업데이트
if [ ! -d "venv" ]; then
    python3.9 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Django Oracle 백엔드 패치 (oracledb 사용하도록)
echo ""
echo "[4.5/7] Django Oracle 백엔드 패치 중..."
if [ -f "$DEPLOY_DIR/patch_django_oracle.sh" ]; then
    chmod +x $DEPLOY_DIR/patch_django_oracle.sh
    bash $DEPLOY_DIR/patch_django_oracle.sh || {
        echo "⚠️  패치 스크립트 실행 실패. 수동 패치가 필요할 수 있습니다."
        echo "   Django Oracle 백엔드 파일을 직접 수정해주세요."
    }
else
    echo "⚠️  patch_django_oracle.sh 파일을 찾을 수 없습니다. 수동으로 패치가 필요할 수 있습니다."
fi

# 5. Frontend 설정
echo ""
echo "[5/7] Frontend 환경 설정 중..."
cd $DEPLOY_DIR/frontend
npm install
npm run build

# 6. Database 마이그레이션
echo ""
echo "[6/7] Database 마이그레이션 실행 중..."
cd $DEPLOY_DIR/backend
source venv/bin/activate

# 로그 디렉토리 생성
mkdir -p $DEPLOY_DIR/logs
chmod 755 $DEPLOY_DIR/logs
chown adm1003701:adm1003701 $DEPLOY_DIR/logs

# 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# 마이그레이션 실행
python manage.py migrate

# 7. 데이터베이스 복원 (덤프 파일이 있는 경우)
echo ""
echo "[7/7] 데이터베이스 복원 확인 중..."
cd $DEPLOY_DIR

# 가장 최근 덤프 파일 찾기
LATEST_DUMP=$(ls -t db_dumps/db_dump_*.json 2>/dev/null | head -n 1)

if [ -n "$LATEST_DUMP" ] && [ -f "$LATEST_DUMP" ]; then
    echo "덤프 파일 발견: $LATEST_DUMP"
    echo "데이터베이스를 복원하시겠습니까? (yes/no)"
    read -r RESTORE_CONFIRM
    
    if [ "$RESTORE_CONFIRM" = "yes" ]; then
        echo "데이터베이스 복원 중..."
        chmod +x import_db.sh
        ./import_db.sh "$LATEST_DUMP"
    else
        echo "데이터베이스 복원을 건너뜁니다."
    fi
else
    echo "덤프 파일을 찾을 수 없습니다. 데이터 복원을 건너뜁니다."
fi

echo ""
echo "========================================"
echo "✅ 배포 완료!"
echo "========================================"
echo ""
echo "Backend: http://192.168.99.37:8000"
echo "Frontend: http://192.168.99.37:3000"
echo ""
echo "서비스를 재시작하려면:"
echo "  cd $DEPLOY_DIR/backend"
echo "  source venv/bin/activate"
echo "  nohup python manage.py runserver 0.0.0.0:8000 > backend.log 2>&1 &"
echo ""
echo "  cd $DEPLOY_DIR/frontend"
echo "  nohup npm start > frontend.log 2>&1 &"
echo ""

