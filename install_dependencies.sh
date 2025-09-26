#!/bin/bash

# 운영서버 의존성 설치 스크립트
# Oracle Linux 8.6용

echo "=== 운영서버 의존성 설치 시작 ==="

# 1. 시스템 업데이트
echo "1. 시스템 업데이트..."
sudo dnf update -y

# 2. 개발 도구 설치
echo "2. 개발 도구 설치..."
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y gcc gcc-c++ make

# 3. Python 3.9 설치
echo "3. Python 3.9 설치..."
sudo dnf install -y python3.9 python3.9-pip python3.9-venv python3.9-devel

# Python 버전 확인
echo "Python 버전:"
python3.9 --version

# 4. Node.js 18 설치
echo "4. Node.js 18 설치..."
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# Node.js 버전 확인
echo "Node.js 버전:"
node --version
npm --version

# 5. Oracle Instant Client 설치 (이미 Oracle DB가 설치되어 있으므로 건너뛸 수 있음)
echo "5. Oracle Instant Client 확인..."
if [ -d "/u01/app/oracle/product/19c/db_1" ]; then
    echo "Oracle Database가 이미 설치되어 있습니다."
    echo "ORACLE_HOME: /u01/app/oracle/product/19c/db_1"
else
    echo "Oracle Instant Client 설치..."
    sudo dnf install -y oracle-instantclient-basic oracle-instantclient-devel
fi

# 6. 방화벽 포트 열기
echo "6. 방화벽 설정..."
sudo firewall-cmd --permanent --add-port=8000/tcp  # Django
sudo firewall-cmd --permanent --add-port=3000/tcp  # Next.js
sudo firewall-cmd --reload

echo "=== 의존성 설치 완료 ==="
echo ""
echo "다음 단계:"
echo "1. 소스코드를 /opt/sales-portal에 복사"
echo "2. Backend 설정: cd /opt/sales-portal/backend && python3.9 -m venv venv"
echo "3. Frontend 설정: cd /opt/sales-portal/frontend && npm install"
