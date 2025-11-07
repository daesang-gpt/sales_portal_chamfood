# 운영서버 시작 가이드

## 📋 개요

운영서버에서 백엔드와 프론트엔드를 백그라운드로 실행하는 완전한 가이드입니다.
**SSH 세션이 끊어져도 서버는 계속 실행됩니다.**

---

## ✅ 사전 준비사항 체크리스트

서버를 시작하기 전에 다음 사항들을 확인하세요:

### 필수 확인 사항

- [ ] **서버 접속**: SSH로 운영서버에 접속했는가?
- [ ] **프로젝트 위치**: `/opt/sales-portal` 디렉토리가 존재하는가?
- [ ] **Backend 가상환경**: `/opt/sales-portal/backend/venv` 디렉토리가 존재하는가?
- [ ] **Frontend 빌드**: `/opt/sales-portal/frontend/.next` 디렉토리가 존재하는가? (없으면 자동 빌드됨)
- [ ] **포트 사용 여부**: 8000번(Backend), 3000번(Frontend) 포트가 사용 중이 아닌가?
- [ ] **데이터베이스 연결**: Oracle DB가 정상 작동 중인가?
- [ ] **환경변수**: Oracle 환경변수가 설정되어 있는가?

### 빠른 확인 방법

```bash
# 사전 준비사항 자동 확인 스크립트 실행
cd /opt/sales-portal
chmod +x check_prerequisites.sh  # 최초 1회만
./check_prerequisites.sh

# 경고사항이 있으면 자동 수정 (실행 권한 부여 등)
./check_prerequisites.sh --fix
```

---

## 🚀 단계별 실행 가이드

### 1단계: 서버 접속 및 프로젝트 디렉토리 이동

```bash
# SSH로 서버 접속 (예시)
ssh adm1003701@192.168.99.37

# 프로젝트 디렉토리로 이동
cd /opt/sales-portal

# 현재 상태 확인
./status.sh
```

**예상 결과**: 서버가 실행 중이 아니면 "실행 중이 아님" 메시지가 표시됩니다.

### 2단계: 실행 권한 부여 (최초 1회만)

```bash
# 방법 1: 모든 스크립트에 실행 권한 부여 (권장)
chmod +x *.sh

# 방법 2: check_prerequisites.sh의 자동 수정 기능 사용
./check_prerequisites.sh --fix

# 확인
ls -l *.sh
```

**예상 결과**: 모든 `.sh` 파일에 `x` 권한이 부여됩니다.

**참고**: `check_prerequisites.sh`를 실행했을 때 실행 권한 경고가 나오면, `--fix` 옵션을 사용하여 자동으로 권한을 부여할 수 있습니다.

### 3단계: 사전 준비사항 확인

```bash
# 자동 확인 스크립트 실행
./check_prerequisites.sh

# 경고사항이 있으면 자동 수정 (실행 권한 부여 등)
./check_prerequisites.sh --fix
```

**예상 결과**: 
- 모든 확인 항목이 통과되어야 합니다. 
- 경고사항이 있으면 `--fix` 옵션으로 자동 수정하거나 수동으로 해결하세요.
- 오류가 있으면 반드시 해결한 후 진행하세요.

**경고사항 해석**:
- ⚠️ **ORACLE_HOME 환경변수 경고**: 스크립트에서 자동으로 설정되므로 무시해도 됩니다.
- ⚠️ **실행 권한 경고**: `./check_prerequisites.sh --fix` 또는 `chmod +x *.sh`로 해결하세요.

### 4단계: 기존 서버 중지 (실행 중인 경우)

```bash
# 현재 실행 상태 확인
./status.sh

# 실행 중인 서버가 있다면 중지
./stop_all.sh
```

**예상 결과**: "모든 서버가 중지되었습니다!" 메시지가 표시됩니다.

### 5단계: 서버 시작

#### 방법 1: 모든 서버 한 번에 시작 (권장)

```bash
./start_all_daemon.sh
```

#### 방법 2: 개별 서버 시작

```bash
# Backend만 시작
./start_backend_daemon.sh

# Frontend만 시작 (Backend 시작 후)
./start_frontend_daemon.sh
```

**예상 결과**: 
- "Backend가 백그라운드에서 시작되었습니다."
- "Frontend가 백그라운드에서 시작되었습니다."
- PID 번호가 표시됩니다.

### 6단계: 서버 상태 확인

```bash
# 상태 확인
./status.sh
```

**예상 결과**:
```
[Backend]
  상태: ✅ 실행 중
  PID: 12345
  포트 8000: ✅ 열림
  메모리: 150.5 MB

[Frontend]
  상태: ✅ 실행 중
  PID: 12346
  포트 3000: ✅ 열림
  메모리: 200.3 MB
```

### 7단계: 로그 확인

```bash
# Backend 로그 실시간 확인
tail -f /opt/sales-portal/logs/backend.log

# Frontend 로그 실시간 확인 (다른 터미널에서)
tail -f /opt/sales-portal/logs/frontend.log
```

**예상 결과**: 정상적으로 시작되었다면 에러 없이 로그가 출력됩니다.

### 8단계: 브라우저에서 접속 확인

- **Backend API**: http://192.168.99.37:8000
- **Frontend**: http://192.168.99.37:3000

**예상 결과**: 
- Backend: Django REST API 응답 확인
- Frontend: 웹 페이지가 정상적으로 로드됨

---

## 📝 상세 설명

### 백그라운드 실행이란?

- **일반 실행**: SSH 세션이 끊어지면 서버도 종료됩니다
- **백그라운드 실행 (nohup)**: SSH 세션이 끊어져도 서버는 계속 실행됩니다 ✅

### 실행 스크립트 동작 방식

1. **프로세스 중복 실행 방지**: 이미 실행 중인 서버가 있으면 시작하지 않습니다
2. **자동 빌드**: Frontend 빌드가 없으면 자동으로 빌드를 시도합니다
3. **로그 저장**: 모든 출력은 `/opt/sales-portal/logs/` 디렉토리에 저장됩니다
4. **PID 관리**: 프로세스 ID를 파일로 저장하여 관리합니다

### 프로세스 확인 방법

```bash
# Backend 프로세스 확인
ps aux | grep "manage.py runserver"

# Frontend 프로세스 확인
ps aux | grep "next start"

# 포트 사용 확인
netstat -tuln | grep -E "8000|3000"
# 또는
ss -tuln | grep -E "8000|3000"
```

---

## 🔄 재시작 방법

### 완전 재시작 (권장)

```bash
# 1. 모든 서버 중지
./stop_all.sh

# 2. 잠시 대기 (포트 해제 대기)
sleep 3

# 3. 모든 서버 시작
./start_all_daemon.sh

# 4. 상태 확인
./status.sh
```

### 개별 재시작

```bash
# Backend만 재시작
./stop_backend.sh
sleep 2
./start_backend_daemon.sh

# Frontend만 재시작
./stop_frontend.sh
sleep 2
./start_frontend_daemon.sh
```

---

## 📊 모니터링

### 로그 모니터링

#### 실시간 로그 확인

```bash
# Backend 로그 실시간 확인
tail -f /opt/sales-portal/logs/backend.log

# Frontend 로그 실시간 확인
tail -f /opt/sales-portal/logs/frontend.log

# 두 로그 동시 확인 (screen/tmux 사용 권장)
```

#### 로그 파일 크기 확인

```bash
# 로그 파일 크기 확인
ls -lh /opt/sales-portal/logs/

# 큰 로그 파일 찾기 (100MB 이상)
find /opt/sales-portal/logs -name "*.log" -size +100M
```

#### 최근 로그 확인

```bash
# Backend 최근 50줄
tail -n 50 /opt/sales-portal/logs/backend.log

# Frontend 최근 50줄
tail -n 50 /opt/sales-portal/logs/frontend.log

# 에러만 확인
grep -i error /opt/sales-portal/logs/backend.log | tail -20
grep -i error /opt/sales-portal/logs/frontend.log | tail -20
```

### 성능 모니터링

#### CPU 및 메모리 사용량 확인

```bash
# 프로세스별 리소스 사용량
ps aux | grep -E "manage.py|next" | grep -v grep

# 전체 시스템 리소스 확인
top
# 또는
htop  # 설치되어 있는 경우
```

#### 디스크 사용량 확인

```bash
# 프로젝트 디렉토리 크기
du -sh /opt/sales-portal

# 로그 디렉토리 크기
du -sh /opt/sales-portal/logs

# 디스크 여유 공간 확인
df -h /opt
```

#### 네트워크 연결 확인

```bash
# 활성 연결 확인
netstat -an | grep -E "8000|3000"

# 연결 수 확인
netstat -an | grep -E ":8000|:3000" | wc -l
```

---

## 💡 실용적인 팁

### 1. Screen 사용법 (세션 관리)

Screen을 사용하면 SSH 세션이 끊어져도 로그를 계속 확인할 수 있습니다.

#### Screen 설치 (필요시)

```bash
# Oracle Linux / RHEL / CentOS
yum install screen -y

# Ubuntu / Debian
apt-get install screen -y
```

#### Screen 사용 방법

```bash
# Screen 세션 생성 및 시작
screen -S sales-portal

# 세션 내에서 로그 확인
tail -f /opt/sales-portal/logs/backend.log

# Screen 세션에서 나가기 (세션은 유지됨)
# Ctrl + A, 그 다음 D 키

# Screen 세션 목록 확인
screen -ls

# Screen 세션 다시 접속
screen -r sales-portal

# Screen 세션 종료
screen -X -S sales-portal quit
```

**Screen 단축키**:
- `Ctrl + A, D`: 세션에서 나가기 (detach)
- `Ctrl + A, C`: 새 창 생성
- `Ctrl + A, N`: 다음 창으로 이동
- `Ctrl + A, P`: 이전 창으로 이동
- `Ctrl + A, "`: 창 목록 보기

### 2. Tmux 사용법 (더 강력한 세션 관리)

Tmux는 Screen보다 더 많은 기능을 제공합니다.

#### Tmux 설치 (필요시)

```bash
# Oracle Linux / RHEL / CentOS
yum install tmux -y

# Ubuntu / Debian
apt-get install tmux -y
```

#### Tmux 사용 방법

```bash
# Tmux 세션 생성 및 시작
tmux new -s sales-portal

# 세션 내에서 로그 확인
tail -f /opt/sales-portal/logs/backend.log

# Tmux 세션에서 나가기 (세션은 유지됨)
# Ctrl + B, 그 다음 D 키

# Tmux 세션 목록 확인
tmux ls

# Tmux 세션 다시 접속
tmux attach -t sales-portal

# Tmux 세션 종료
tmux kill-session -t sales-portal
```

**Tmux 단축키**:
- `Ctrl + B, D`: 세션에서 나가기 (detach)
- `Ctrl + B, C`: 새 창 생성
- `Ctrl + B, N`: 다음 창으로 이동
- `Ctrl + B, P`: 이전 창으로 이동
- `Ctrl + B, %`: 세로 분할
- `Ctrl + B, "`: 가로 분할
- `Ctrl + B, 화살표`: 분할 창 간 이동

### 3. 자동 재시작 설정

서버가 비정상 종료되었을 때 자동으로 재시작하는 방법입니다.

#### 간단한 자동 재시작 스크립트 생성

```bash
# 자동 재시작 스크립트 생성
cat > /opt/sales-portal/auto_restart.sh << 'EOF'
#!/bin/bash

PROJECT_ROOT="/opt/sales-portal"

# Backend 확인 및 재시작
if ! pgrep -f "manage.py runserver" > /dev/null; then
    echo "$(date): Backend가 실행 중이 아닙니다. 재시작합니다."
    cd "$PROJECT_ROOT"
    ./start_backend_daemon.sh
fi

# Frontend 확인 및 재시작
if ! pgrep -f "next start\|next-server" > /dev/null; then
    echo "$(date): Frontend가 실행 중이 아닙니다. 재시작합니다."
    cd "$PROJECT_ROOT"
    ./start_frontend_daemon.sh
fi
EOF

chmod +x /opt/sales-portal/auto_restart.sh
```

#### Cron에 자동 재시작 등록

```bash
# Crontab 편집
crontab -e

# 다음 줄 추가 (5분마다 확인)
*/5 * * * * /opt/sales-portal/auto_restart.sh >> /opt/sales-portal/logs/auto_restart.log 2>&1
```

### 4. 서버 재부팅 후 자동 시작 설정

서버가 재부팅되면 자동으로 서버를 시작하도록 설정합니다.

#### 방법 1: Crontab 사용 (간단)

```bash
# Crontab 편집
crontab -e

# 다음 줄 추가 (@reboot는 재부팅 시 실행)
@reboot sleep 30 && cd /opt/sales-portal && ./start_all_daemon.sh >> /opt/sales-portal/logs/startup.log 2>&1
```

#### 방법 2: Systemd 서비스 생성 (권장)

```bash
# Backend 서비스 파일 생성
cat > /etc/systemd/system/sales-portal-backend.service << 'EOF'
[Unit]
Description=Sales Portal Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sales-portal/backend
Environment="ORACLE_HOME=/u01/app/oracle/product/19c/db_1"
Environment="LD_LIBRARY_PATH=/u01/app/oracle/product/19c/db_1/lib"
Environment="PATH=/u01/app/oracle/product/19c/db_1/bin:$PATH"
Environment="DJANGO_SETTINGS_MODULE=settings.production"
Environment="DB_NAME=192.168.99.37:1521/XEPDB1"
Environment="DB_USER=salesportal"
Environment="DB_PASSWORD=salesportal123"
ExecStart=/opt/sales-portal/backend/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10
StandardOutput=append:/opt/sales-portal/logs/backend.log
StandardError=append:/opt/sales-portal/logs/backend.log

[Install]
WantedBy=multi-user.target
EOF

# Frontend 서비스 파일 생성
cat > /etc/systemd/system/sales-portal-frontend.service << 'EOF'
[Unit]
Description=Sales Portal Frontend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sales-portal/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=append:/opt/sales-portal/logs/frontend.log
StandardError=append:/opt/sales-portal/logs/frontend.log

[Install]
WantedBy=multi-user.target
EOF

# 서비스 활성화
systemctl daemon-reload
systemctl enable sales-portal-backend
systemctl enable sales-portal-frontend

# 서비스 시작
systemctl start sales-portal-backend
systemctl start sales-portal-frontend

# 서비스 상태 확인
systemctl status sales-portal-backend
systemctl status sales-portal-frontend
```

**Systemd 서비스 관리 명령어**:
```bash
# 서비스 시작
systemctl start sales-portal-backend
systemctl start sales-portal-frontend

# 서비스 중지
systemctl stop sales-portal-backend
systemctl stop sales-portal-frontend

# 서비스 재시작
systemctl restart sales-portal-backend
systemctl restart sales-portal-frontend

# 서비스 상태 확인
systemctl status sales-portal-backend
systemctl status sales-portal-frontend

# 서비스 로그 확인
journalctl -u sales-portal-backend -f
journalctl -u sales-portal-frontend -f
```

### 5. 방화벽 확인

서버가 외부에서 접근 가능한지 확인합니다.

```bash
# 방화벽 상태 확인 (firewalld 사용 시)
firewall-cmd --list-all

# 포트 열기 (필요시)
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --reload

# 방화벽 상태 확인 (iptables 사용 시)
iptables -L -n | grep -E "8000|3000"

# 포트 열기 (iptables 사용 시)
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
service iptables save
```

### 6. 로그 로테이션 설정

로그 파일이 너무 커지지 않도록 로그 로테이션을 설정합니다.

```bash
# Logrotate 설정 파일 생성
cat > /etc/logrotate.d/sales-portal << 'EOF'
/opt/sales-portal/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0644 root root
    sharedscripts
    postrotate
        # 서버 재시작 없이 로그 파일 재생성
        /bin/kill -USR1 $(cat /opt/sales-portal/logs/backend.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

# 설정 테스트
logrotate -d /etc/logrotate.d/sales-portal

# 수동 실행
logrotate -f /etc/logrotate.d/sales-portal
```

### 7. 성능 최적화 팁

#### Backend 성능 모니터링

```bash
# Django 쿼리 로깅 활성화 (settings.production.py에서)
# DEBUG = True로 설정하면 모든 쿼리가 로그에 기록됨

# 느린 쿼리 확인
grep "slow" /opt/sales-portal/logs/backend.log

# 메모리 누수 확인
ps aux | grep "manage.py runserver" | awk '{print $6/1024 " MB"}'
```

#### Frontend 성능 모니터링

```bash
# 빌드 최적화 확인
cd /opt/sales-portal/frontend
npm run build

# 빌드 결과 확인 (.next 폴더 크기)
du -sh .next
```

---

## 🆘 문제 해결

### check_prerequisites.sh 경고사항 해결

#### 실행 권한 경고 해결

`check_prerequisites.sh` 실행 시 다음과 같은 경고가 나오는 경우:

```
⚠️ start_backend_daemon.sh 실행 권한이 없습니다
⚠️ start_frontend_daemon.sh 실행 권한이 없습니다
...
```

**해결 방법**:

```bash
# 방법 1: 자동 수정 (권장)
./check_prerequisites.sh --fix

# 방법 2: 수동 수정
chmod +x *.sh

# 확인
./check_prerequisites.sh
```

#### ORACLE_HOME 환경변수 경고

다음 경고는 무시해도 됩니다:

```
⚠️ ORACLE_HOME 환경변수가 설정되어 있지 않습니다
   스크립트에서 자동으로 설정됩니다
```

이 경고는 정상입니다. 실행 스크립트(`start_backend_daemon.sh` 등)에서 자동으로 Oracle 환경변수를 설정하므로, 미리 설정하지 않아도 됩니다.

### 서버가 시작되지 않는 경우

#### 1. 포트가 이미 사용 중인지 확인

```bash
# 포트 사용 확인
netstat -tuln | grep -E "8000|3000"
# 또는
ss -tuln | grep -E "8000|3000"

# 포트를 사용하는 프로세스 확인
lsof -i :8000
lsof -i :3000
# 또는
fuser 8000/tcp
fuser 3000/tcp
```

**해결 방법**: 포트를 사용하는 프로세스를 종료하거나 다른 포트 사용

```bash
# 프로세스 강제 종료
kill -9 $(lsof -t -i:8000)
kill -9 $(lsof -t -i:3000)
```

#### 2. 로그 확인

```bash
# Backend 로그 확인
tail -n 100 /opt/sales-portal/logs/backend.log

# Frontend 로그 확인
tail -n 100 /opt/sales-portal/logs/frontend.log

# 에러만 확인
grep -i error /opt/sales-portal/logs/backend.log | tail -20
grep -i error /opt/sales-portal/logs/frontend.log | tail -20
```

#### 3. 데이터베이스 연결 확인

```bash
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# DB 연결 테스트
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('DB 연결 성공!')"
```

#### 4. 프로세스 강제 종료 후 재시작

```bash
# 모든 관련 프로세스 강제 종료
pkill -9 -f "manage.py runserver"
pkill -9 -f "next start"
pkill -9 -f "next-server"

# PID 파일 삭제
rm -f /opt/sales-portal/logs/backend.pid
rm -f /opt/sales-portal/logs/frontend.pid

# 재시작
cd /opt/sales-portal
./start_all_daemon.sh
```

### 서버가 자주 종료되는 경우

#### 1. 메모리 부족 확인

```bash
# 메모리 사용량 확인
free -h

# 메모리 사용량이 높으면 프로세스 확인
ps aux --sort=-%mem | head -10
```

#### 2. 디스크 공간 확인

```bash
# 디스크 사용량 확인
df -h

# 로그 파일 크기 확인
du -sh /opt/sales-portal/logs/*
```

#### 3. 자동 재시작 로그 확인

```bash
# 자동 재시작 로그 확인 (설정한 경우)
tail -f /opt/sales-portal/logs/auto_restart.log
```

### Frontend 빌드 실패

```bash
cd /opt/sales-portal/frontend

# node_modules 재설치
rm -rf node_modules
npm install

# 빌드 재시도
npm run build

# 빌드 로그 확인
npm run build 2>&1 | tee build.log
```

### Backend 가상환경 문제

```bash
cd /opt/sales-portal/backend

# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 추가 리소스

- **배포 가이드**: `DEPLOYMENT_GUIDE.md` 참조
- **운영 가이드**: `OPERATIONS_GUIDE.md` 참조
- **마이그레이션 관리**: `MIGRATION_MANAGEMENT.md` 참조

---

## 🔗 빠른 참조

### 자주 사용하는 명령어

```bash
# 사전 준비사항 확인
./check_prerequisites.sh

# 경고사항 자동 수정
./check_prerequisites.sh --fix

# 상태 확인
./status.sh

# 모든 서버 시작
./start_all_daemon.sh

# 모든 서버 중지
./stop_all.sh

# Backend 로그 확인
tail -f /opt/sales-portal/logs/backend.log

# Frontend 로그 확인
tail -f /opt/sales-portal/logs/frontend.log

# 프로세스 확인
ps aux | grep -E "manage.py|next"
```

### 서버 주소

- **Backend API**: http://192.168.99.37:8000
- **Frontend**: http://192.168.99.37:3000
- **API 문서**: http://192.168.99.37:8000/api/docs (설정된 경우)

---

**마지막 업데이트**: 2024년
