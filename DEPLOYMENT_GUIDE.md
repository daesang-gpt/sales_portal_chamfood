# 운영서버 배포 가이드

## 서버 접속 정보
- **서버 OS**: Oracle Linux 8.6
- **서버 hostname**: dslspdev
- **서버 IP**: 192.168.99.37
- **서버 계정**: adm1003701 / dsit_459037&
- **Root 계정**: root / dsit_459037&
- **접속 방법**: SSH로 adm1003701 계정 접속 후 `su - root`로 전환

## Oracle Database 설치 정보
- **구성**: Single
- **DBMS**: Oracle 19.20 EE
- **Oracle Home**: /u01/app/oracle/product/19c/db_1
- **Data Directory**: /oradata
- **Archive Log Directory**: /oraarch
- **Listener Port**: 1521
- **SID**: XEPDB1 (확인 필요 - PDB 이름일 가능성)
- **Character Set**: AL32UTF8
- **System Password**: Welcome123

## 파일시스템 구성
- `/u01`: Oracle 소프트웨어
- `/oradata`: 데이터 파일
- `/oraarch`: 아카이브 로그

## ✅ 확인 완료된 사항

### 1. Database 연결 정보 (확인 완료)
- **SID**: XEPDB1 (non-CDB 구성)
- **PDB**: 없음 (단일 인스턴스)
- **현재 Django 설정**: ✅ 올바름
- **리스너 서비스**: XEPDB1 정상 동작

### 2. 사용자 계정 (생성 완료)
- **사용자명**: salesportal ✅
- **비밀번호**: salesportal123 ✅
- **계정 상태**: OPEN ✅
- **권한**: CONNECT, RESOURCE, CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE VIEW ✅
- **테이블스페이스**: USERS (UNLIMITED) ✅

## 환경변수 설정

### 운영서버 환경변수 (.bashrc 또는 .profile에 추가)
```bash
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export ORACLE_SID=XEPDB1  # 실제 SID로 변경 필요
export PATH=$ORACLE_HOME/bin:$PATH
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
```

### Django 애플리케이션 환경변수
```bash
export DJANGO_SETTINGS_MODULE=settings.production
export SECRET_KEY=your-production-secret-key-here
export ALLOWED_HOSTS=192.168.99.37,dslspdev
export DB_NAME=192.168.99.37:1521/XEPDB1  # 실제 연결 정보로 수정 필요
export DB_USER=salesportal
export DB_PASSWORD=salesportal123
```

## 소프트웨어 설치 단계

### 1. Python 3.9+ 설치 (Oracle Linux 8.6)
```bash
# 시스템 업데이트
sudo dnf update -y

# Python 3.9 설치
sudo dnf install -y python3.9 python3.9-pip python3.9-venv python3.9-dev

# Python 버전 확인
python3.9 --version
```

### 2. Node.js 18+ 설치 (Next.js용)
```bash
# NodeSource 저장소 추가
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -

# Node.js 설치
sudo dnf install -y nodejs

# 버전 확인
node --version
npm --version
```

### 3. Oracle Instant Client 설치 (cx_Oracle용)
```bash
# Oracle Instant Client RPM 다운로드 및 설치
sudo dnf install -y oracle-instantclient-basic oracle-instantclient-devel oracle-instantclient-sqlplus

# 또는 수동 설치
wget https://download.oracle.com/otn_software/linux/instantclient/1920000/oracle-instantclient-basic-19.20.0.0.0-1.x86_64.rpm
sudo rpm -ivh oracle-instantclient-basic-19.20.0.0.0-1.x86_64.rpm
```

## 애플리케이션 배포 단계

### 1. 소스코드 배포
```bash
# 로컬에서 서버로 소스코드 전송
scp -r C:\Users\ds\Projects\sales-portal adm1003701@192.168.99.37:/home/adm1003701/

# 서버에서 적절한 위치로 이동
sudo mv /home/adm1003701/sales-portal /opt/
sudo chown -R adm1003701:adm1003701 /opt/sales-portal
```

### 2. Backend (Django) 설정
```bash
cd /opt/sales-portal/backend

# Python 가상환경 생성
python3.9 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Oracle 환경변수 설정 (cx_Oracle용)
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
```

### 3. Frontend (Next.js) 설정
```bash
cd /opt/sales-portal/frontend

# 의존성 설치
npm install

# 프로덕션 빌드
npm run build
```

### 4. Database 마이그레이션
```bash
cd /opt/sales-portal/backend
source venv/bin/activate

# 연결 테스트
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('DB 연결 성공!')"

# 마이그레이션 실행
python manage.py migrate
```

### 5. 애플리케이션 시작
```bash
# Backend 시작 (백그라운드)
cd /opt/sales-portal/backend
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 > backend.log 2>&1 &

# Frontend 시작 (백그라운드)
cd /opt/sales-portal/frontend
nohup npm start > frontend.log 2>&1 &
```

## 주의사항
1. **Database 연결 정보 재확인 필요**: XEPDB1이 실제 SID인지 PDB 이름인지 확인
2. **방화벽 설정**: 8000 포트 오픈 확인
3. **Oracle Client 설치**: cx_Oracle 사용을 위한 Oracle Instant Client 설치 필요
4. **로그 디렉토리**: `/path/to/logs` 디렉토리 생성 및 권한 설정

## 트러블슈팅
- Oracle 연결 오류 시 tnsping으로 연결 테스트
- 권한 오류 시 사용자 권한 재확인
- 포트 접근 오류 시 방화벽 설정 확인
