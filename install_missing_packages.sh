#!/bin/bash

# 누락된 Python 패키지들 설치 스크립트

echo "=== 🚀 누락된 Python 패키지 설치 시작 ==="

cd /opt/sales-portal/backend

# 가상환경 활성화
source venv/bin/activate

echo "현재 Python 버전:"
python --version

echo "현재 pip 버전:"
pip --version

# pip 업그레이드
echo "pip 업그레이드 중..."
pip install --upgrade pip

echo "=== 1. 로그 디렉토리 생성 ==="
mkdir -p /opt/sales-portal/logs
chmod 755 /opt/sales-portal/logs
chown adm1003701:adm1003701 /opt/sales-portal/logs

echo "=== 2. 누락된 패키지들 설치 ==="

# AI/ML 패키지들 (KeyBERT 및 의존성)
echo "KeyBERT 및 의존성 설치 중... (시간이 오래 걸릴 수 있습니다)"
pip install keybert>=0.8.0
pip install sentence-transformers>=2.2.0
pip install transformers>=4.21.0
pip install torch>=1.12.0 --index-url https://download.pytorch.org/whl/cpu
pip install numpy>=1.21.0
pip install scikit-learn>=1.1.0

# 기타 누락 패키지들
echo "기타 패키지들 설치 중..."
pip install requests>=2.28.0
pip install bcrypt>=4.0.0

echo "=== 3. 설치된 패키지 확인 ==="
pip list | grep -E "(keybert|sentence-transformers|torch|numpy|scikit-learn)"

echo "=== 4. Django 설정 테스트 ==="

# Oracle 환경변수 설정
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

# Django 환경변수 설정
export DJANGO_SETTINGS_MODULE=settings.production
export SECRET_KEY=your-production-secret-key-here
export ALLOWED_HOSTS=192.168.99.37,dslspdev
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

echo "Django 설정 검사 중..."
python manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Django 설정 검사 통과!"
    
    echo "=== 5. 데이터베이스 연결 테스트 ==="
    python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('✅ DB 연결 성공!')"
    
    if [ $? -eq 0 ]; then
        echo "✅ 데이터베이스 연결 성공!"
        
        echo "=== 6. 마이그레이션 실행 ==="
        python manage.py migrate
        
        if [ $? -eq 0 ]; then
            echo "🎉 모든 설정 완료! Django Backend 준비됨!"
        else
            echo "❌ 마이그레이션 실패"
        fi
    else
        echo "❌ 데이터베이스 연결 실패"
    fi
else
    echo "❌ Django 설정 검사 실패"
fi

echo "=== 설치 완료 ==="


