# 운영 서버 완전 삭제 가이드

⚠️ **경고**: 이 작업은 되돌릴 수 없습니다! 신중하게 진행하세요.

## 사전 확인 사항

삭제하기 전에 반드시 확인하세요:

1. ✅ **백업 확인**: 로컬에 최신 백업 파일이 있는지 확인
2. ✅ **데이터베이스 백업**: DB 데이터가 로컬에 백업되어 있는지 확인
3. ✅ **코드 백업**: 소스코드가 Git에 푸시되어 있는지 확인
4. ✅ **서비스 중지**: 다른 사용자가 서비스를 사용하지 않는지 확인

## 삭제되는 항목

다음 항목들이 완전히 삭제됩니다:

1. **프로젝트 디렉토리**: `/opt/sales-portal`
   - 모든 소스코드
   - 모든 설정 파일
   - 모든 스크립트 파일 (.sh, .ps1)

2. **백업 파일**: `/opt/sales-portal/db_dumps`
   - 모든 DB 덤프 파일

3. **로그 파일**: `/opt/sales-portal/logs`
   - 모든 로그 파일

4. **실행 중인 프로세스**
   - Backend (Django) 프로세스
   - Frontend (Next.js) 프로세스

5. **Cron 작업**
   - 등록된 모든 cron 작업

6. **데이터베이스 데이터** (선택사항)
   - 모든 테이블
   - 모든 시퀀스
   - 모든 뷰

## 사용 방법

### 방법 1: Bash 스크립트 사용

```bash
# 실행 권한 부여 (처음 한 번만)
chmod +x wipe_production_server.sh

# 스크립트 실행
./wipe_production_server.sh
```

**확인 과정**:
1. 첫 번째 확인: `yes` 입력
2. 두 번째 확인: `DELETE ALL` 입력
3. 데이터베이스 삭제 여부 선택

### 방법 2: PowerShell 스크립트 사용

```powershell
# 일반 실행 (확인 과정 포함)
.\wipe_production_server.ps1

# 강제 실행 (확인 없이 바로 실행 - 위험!)
.\wipe_production_server.ps1 -Force
```

## 삭제 단계

스크립트는 다음 순서로 삭제를 진행합니다:

1. **실행 중인 프로세스 중지**
   - Backend 프로세스 종료
   - Frontend 프로세스 종료

2. **Cron 작업 제거**
   - Django crontab 제거

3. **프로젝트 디렉토리 삭제**
   - `/opt/sales-portal` 전체 삭제

4. **로그 디렉토리 삭제**
   - `/opt/sales-portal/logs` 삭제

5. **백업 디렉토리 삭제**
   - `/opt/sales-portal/db_dumps` 삭제

6. **남은 파일 확인 및 정리**
   - 남은 파일 강제 삭제
   - 남은 프로세스 강제 종료

7. **데이터베이스 삭제** (선택사항)
   - 모든 테이블 삭제
   - 모든 시퀀스 삭제
   - 모든 뷰 삭제

## 수동 삭제 방법

스크립트를 사용하지 않고 수동으로 삭제하려면:

### 1. 서버 접속

```bash
ssh adm1003701@192.168.99.37
```

### 2. 프로세스 중지

```bash
# Backend 프로세스 중지
pkill -f "python.*manage.py runserver"

# Frontend 프로세스 중지
pkill -f "node.*next"
pkill -f "npm.*start"
```

### 3. Cron 작업 제거

```bash
cd /opt/sales-portal/backend
source venv/bin/activate
python manage.py crontab remove
```

### 4. 디렉토리 삭제

```bash
# 프로젝트 디렉토리 삭제
sudo rm -rf /opt/sales-portal

# 로그 디렉토리 삭제 (혹시 남아있다면)
sudo rm -rf /opt/sales-portal/logs

# 백업 디렉토리 삭제 (혹시 남아있다면)
sudo rm -rf /opt/sales-portal/db_dumps
```

### 5. 데이터베이스 삭제 (선택사항)

```bash
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export PATH=$ORACLE_HOME/bin:$PATH
export ORACLE_SID=XEPDB1

sqlplus salesportal/salesportal123 <<EOF
-- 모든 테이블 삭제
BEGIN
  FOR cur_rec IN (SELECT object_name, object_type FROM user_objects WHERE object_type = 'TABLE') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP TABLE ' || cur_rec.object_name || ' CASCADE CONSTRAINTS';
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

-- 모든 시퀀스 삭제
BEGIN
  FOR cur_rec IN (SELECT object_name FROM user_objects WHERE object_type = 'SEQUENCE') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP SEQUENCE ' || cur_rec.object_name;
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

-- 모든 뷰 삭제
BEGIN
  FOR cur_rec IN (SELECT object_name FROM user_objects WHERE object_type = 'VIEW') LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP VIEW ' || cur_rec.object_name;
    EXCEPTION
      WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END;
/

EXIT;
EOF
```

## 복구 방법

삭제 후 복구하려면:

1. **코드 복구**: Git에서 다시 클론
   ```bash
   git clone <repository-url> /opt/sales-portal
   ```

2. **데이터 복구**: 로컬 백업 파일을 사용하여 복원
   ```bash
   ./import_db.sh db_dumps/db_dump_YYYYMMDD_HHMMSS.json
   ```

3. **환경 재설정**: 배포 가이드 참조
   - `DEPLOYMENT_GUIDE.md` 참조

## 주의사항

1. ⚠️ **되돌릴 수 없음**: 삭제된 데이터는 복구할 수 없습니다
2. ⚠️ **백업 필수**: 삭제 전 반드시 백업을 확인하세요
3. ⚠️ **서비스 중단**: 삭제 중 서비스가 중단됩니다
4. ⚠️ **권한 확인**: sudo 권한이 필요할 수 있습니다
5. ⚠️ **네트워크 확인**: SSH 연결이 안정적인지 확인하세요

## 문제 해결

### 권한 오류

```bash
# root 권한으로 전환
su - root
# 비밀번호: dsit_459037&
```

### 프로세스가 종료되지 않음

```bash
# 강제 종료
pkill -9 -f "python.*manage.py runserver"
pkill -9 -f "node.*next"
```

### 디렉토리가 삭제되지 않음

```bash
# root 권한으로 강제 삭제
sudo rm -rf /opt/sales-portal
```

## 관련 문서

- `DEPLOYMENT_GUIDE.md` - 배포 가이드
- `DB_DOWNLOAD_GUIDE.md` - DB 백업 가이드
- `OPERATIONS_GUIDE.md` - 운영 가이드

