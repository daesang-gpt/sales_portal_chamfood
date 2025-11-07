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

# 1. 기존 배포 백업 (디스크 공간 확인 후 선택적 백업)
if [ -d "$DEPLOY_DIR" ]; then
    echo ""
    echo "[1/7] 기존 배포 백업 확인 중..."
    # 디스크 공간 확인 (GB 단위, 루트 파티션)
    AVAILABLE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    # 백업 디렉토리 정리 (오래된 백업 삭제)
    if [ -d "/opt" ]; then
        echo "오래된 백업 파일 정리 중..."
        # 최신 2개만 남기고 나머지 삭제
        cd /opt
        ls -t sales-portal-backup-* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true
    fi
    # 공간 확인 후 백업 생성
    if [ "$AVAILABLE_SPACE" -gt 10 ]; then
        echo "백업 생성 중... (사용 가능 공간: ${AVAILABLE_SPACE}GB)"
        sudo cp -r $DEPLOY_DIR $BACKUP_DIR 2>/dev/null || {
            echo "⚠️  백업 생성 실패 (디스크 공간 부족 가능). 계속 진행합니다..."
        }
        if [ -d "$BACKUP_DIR" ]; then
            echo "백업 위치: $BACKUP_DIR"
        fi
    else
        echo "⚠️  디스크 공간 부족 (사용 가능: ${AVAILABLE_SPACE}GB). 백업을 건너뜁니다."
        echo "   필요시 수동으로 백업하세요: cp -r $DEPLOY_DIR $BACKUP_DIR"
    fi
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
echo "마이그레이션 상태 확인 중..."
python manage.py showmigrations myapi | tail -5 || true

# 테이블 존재 여부 확인
echo "데이터베이스 테이블 존재 여부 확인 중..."
TABLE_EXISTS=$(python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute(\"SELECT COUNT(*) FROM user_tables WHERE table_name LIKE 'MYAPI_%'\")
    count = cursor.fetchone()[0]
    print(count)
except:
    print('0')
" 2>/dev/null | tail -1)

if [ "$TABLE_EXISTS" = "0" ] || [ -z "$TABLE_EXISTS" ]; then
    echo "테이블이 없습니다. 마이그레이션 이력을 먼저 fake로 표시한 후 스키마 생성 중..."
    # 먼저 모든 마이그레이션을 fake로 표시 (django_migrations 테이블 생성 및 기록)
    echo "1단계: 모든 마이그레이션을 fake로 표시 중..."
    python manage.py migrate --fake || {
        echo "⚠️  마이그레이션 fake 실패 (정상일 수 있음 - django_migrations 테이블이 없을 수 있음)"
    }
    
    # 그 다음 --run-syncdb로 현재 모델 상태로 테이블 생성
    echo "2단계: --run-syncdb로 스키마 생성 중..."
    python manage.py migrate --run-syncdb || {
        echo "⚠️  --run-syncdb 실패. 대체 방법 시도 중..."
        # 대체 방법: 마이그레이션 없이 테이블만 생성
        python manage.py migrate --fake-initial || {
            echo "❌ 마이그레이션 실패. 수동으로 처리해야 합니다."
            exit 1
        }
    }
else
    echo "테이블이 존재합니다. 마이그레이션 적용 중..."
    # 테이블이 있으면 --fake-initial로 마이그레이션 적용
    # --fake-initial: 초기 마이그레이션이 이미 적용된 것으로 간주 (테이블이 존재하면)
    python manage.py migrate --fake-initial
fi

# 7. 데이터베이스 복원 (덤프 파일이 있는 경우)
echo ""
echo "[7/8] 데이터베이스 복원 확인 중..."
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

# 8. Cron 작업 등록
echo ""
echo "[8/8] Cron 작업 등록 중..."
cd $DEPLOY_DIR/backend
source venv/bin/activate

# 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# Django crontab 등록 (고객 구분 자동 업데이트)
echo "Django crontab 등록 중..."
python manage.py crontab add 2>/dev/null || {
    echo "⚠️  Django crontab 등록 실패 (이미 등록되어 있을 수 있음)"
    echo "   기존 crontab 확인: python manage.py crontab show"
}

# 배치 작업 스크립트에 실행 권한 부여
if [ -f "$DEPLOY_DIR/maintenance_batch.sh" ]; then
    chmod +x "$DEPLOY_DIR/maintenance_batch.sh"
    echo "✅ maintenance_batch.sh 실행 권한 설정 완료"
fi

if [ -f "$DEPLOY_DIR/backup_db.sh" ]; then
    chmod +x "$DEPLOY_DIR/backup_db.sh"
    echo "✅ backup_db.sh 실행 권한 설정 완료"
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
echo "========================================"
echo "Cron 작업 설정 안내"
echo "========================================"
echo ""
echo "다음 명령어로 시스템 crontab에 배치 작업을 추가하세요:"
echo ""
echo "  crontab -e"
echo ""
echo "다음 줄들을 추가하세요:"
echo ""
echo "  # 매일 새벽 3시: 배치 작업 실행"
echo "  0 3 * * * $DEPLOY_DIR/maintenance_batch.sh >> $DEPLOY_DIR/logs/maintenance.log 2>&1"
echo ""
echo "  # 매일 새벽 4시: 데이터베이스 백업"
echo "  0 4 * * * $DEPLOY_DIR/backup_db.sh >> $DEPLOY_DIR/logs/backup.log 2>&1"
echo ""
echo "로그 로테이션 설정:"
echo "  sudo cp $DEPLOY_DIR/logrotate_sales_portal.conf /etc/logrotate.d/sales-portal"
echo "  sudo chmod 644 /etc/logrotate.d/sales-portal"
echo ""
echo "자세한 내용은 OPERATIONS_GUIDE.md를 참조하세요."
echo ""

