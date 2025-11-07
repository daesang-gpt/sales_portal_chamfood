# 운영 가이드 (Operations Guide)

이 문서는 Sales Portal 운영 서버의 배치 작업, Cron 작업, 로그 관리 등에 대한 가이드를 제공합니다.

## 목차

1. [배치 작업 설정](#배치-작업-설정)
2. [Cron 작업 등록](#cron-작업-등록)
3. [로그 로테이션 설정](#로그-로테이션-설정)
4. [수동 실행 방법](#수동-실행-방법)
5. [모니터링 방법](#모니터링-방법)
6. [문제 해결](#문제-해결)

---

## 배치 작업 설정

### 배치 작업 스크립트

운영 서버에는 다음 두 가지 배치 작업 스크립트가 있습니다:

1. **`maintenance_batch.sh`**: 일일 유지보수 작업
   - 오래된 로그 파일 정리 (30일 이상)
   - 만료된 세션 데이터 정리
   - 만료된 JWT 토큰 블랙리스트 정리 (7일 이상)
   - 정적 파일 수집 (`collectstatic`)
   - Oracle DB 통계 업데이트 (성능 최적화)
   - 디스크 공간 확인 및 경고

2. **`backup_db.sh`**: 데이터베이스 백업
   - Django `dumpdata`를 사용한 데이터베이스 백업
   - UTF-8 인코딩 처리
   - 백업 파일명에 타임스탬프 포함
   - 오래된 백업 파일 자동 정리 (30일 이상)
   - 디스크 공간 확인 후 백업 실행

### 스크립트 위치

```
/opt/sales-portal/
├── maintenance_batch.sh    # 배치 작업 스크립트
├── backup_db.sh            # DB 백업 스크립트
└── logs/                   # 로그 디렉토리
    ├── maintenance.log     # 배치 작업 로그
    └── backup.log          # 백업 작업 로그
```

---

## Cron 작업 등록

### 1. Django Crontab 등록 (고객 구분 자동 업데이트)

Django crontab은 배포 스크립트(`deploy_from_git_with_db.sh`)에서 자동으로 등록됩니다.

수동으로 등록하려면:

```bash
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

# Django crontab 등록
python manage.py crontab add

# 등록된 crontab 확인
python manage.py crontab show

# crontab 제거 (필요시)
python manage.py crontab remove
```

**스케줄**: 매일 새벽 2시 (`0 2 * * *`)

### 2. 시스템 Crontab 등록 (배치 작업 및 백업)

시스템 crontab에 배치 작업과 백업 작업을 추가합니다:

```bash
# crontab 편집기 열기
crontab -e

# 다음 줄들을 추가:
# 매일 새벽 3시: 배치 작업 실행
0 3 * * * /opt/sales-portal/maintenance_batch.sh >> /opt/sales-portal/logs/maintenance.log 2>&1

# 매일 새벽 4시: 데이터베이스 백업
0 4 * * * /opt/sales-portal/backup_db.sh >> /opt/sales-portal/logs/backup.log 2>&1
```

**Cron 스케줄 형식**:
```
분 시 일 월 요일 명령어
0   3  *  *  *     /opt/sales-portal/maintenance_batch.sh
```

### 전체 Cron 작업 스케줄

| 시간 | 작업 | 설명 |
|------|------|------|
| 새벽 2시 | 고객 구분 자동 업데이트 | Django crontab (`myapi.cron.update_customer_classifications`) |
| 새벽 3시 | 배치 작업 실행 | `maintenance_batch.sh` |
| 새벽 4시 | 데이터베이스 백업 | `backup_db.sh` |

### Cron 작업 확인

```bash
# 현재 사용자의 crontab 확인
crontab -l

# Django crontab 확인
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
python manage.py crontab show
```

---

## 로그 로테이션 설정

로그 파일이 무한정 증가하는 것을 방지하기 위해 로그 로테이션을 설정합니다.

### 설정 방법

1. **로그 로테이션 설정 파일 복사** (root 권한 필요):

```bash
sudo cp /opt/sales-portal/logrotate_sales_portal.conf /etc/logrotate.d/sales-portal
sudo chmod 644 /etc/logrotate.d/sales-portal
```

2. **설정 확인**:

```bash
# 설정 파일 내용 확인
cat /etc/logrotate.d/sales-portal

# 로그 로테이션 테스트 (실제 로테이션은 하지 않고 테스트만)
sudo logrotate -d /etc/logrotate.d/sales-portal

# 강제로 로그 로테이션 실행 (테스트)
sudo logrotate -f /etc/logrotate.d/sales-portal
```

### 로그 로테이션 설정 내용

- **로테이션 주기**: 매일 (`daily`)
- **보관 기간**: 30일 (`rotate 30`)
- **압축**: 활성화 (`compress`)
- **지연 압축**: 활성화 (`delaycompress` - 다음 로테이션 시 압축)
- **파일 권한**: `0644`, 소유자 `adm1003701:adm1003701`

### 로그 파일 위치

```
/opt/sales-portal/logs/
├── django.log              # Django 애플리케이션 로그
├── maintenance.log          # 배치 작업 로그
├── backup.log               # 백업 작업 로그
├── django.log.1             # 로테이션된 로그 (압축 전)
├── django.log.2.gz         # 로테이션된 로그 (압축 후)
└── ...
```

---

## 수동 실행 방법

### 배치 작업 수동 실행

```bash
cd /opt/sales-portal
./maintenance_batch.sh

# 또는 로그 파일로 출력
./maintenance_batch.sh >> logs/maintenance.log 2>&1
```

### 데이터베이스 백업 수동 실행

```bash
cd /opt/sales-portal
./backup_db.sh

# 또는 로그 파일로 출력
./backup_db.sh >> logs/backup.log 2>&1
```

### 고객 구분 업데이트 수동 실행

```bash
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123

python manage.py update_customer_classifications
```

---

## 모니터링 방법

### 로그 파일 확인

```bash
# 실시간 로그 확인
tail -f /opt/sales-portal/logs/maintenance.log
tail -f /opt/sales-portal/logs/backup.log
tail -f /opt/sales-portal/logs/django.log

# 최근 로그 확인 (마지막 100줄)
tail -n 100 /opt/sales-portal/logs/maintenance.log

# 특정 날짜의 로그 검색
grep "2025-01-15" /opt/sales-portal/logs/maintenance.log
```

### 백업 파일 확인

```bash
# 백업 디렉토리 확인
ls -lh /opt/sales-portal/db_dumps/

# 최근 백업 파일 확인
ls -lt /opt/sales-portal/db_dumps/ | head -10

# 백업 파일 크기 확인
du -sh /opt/sales-portal/db_dumps/
```

### 디스크 공간 확인

```bash
# 전체 디스크 사용량 확인
df -h /

# 특정 디렉토리 크기 확인
du -sh /opt/sales-portal/
du -sh /opt/sales-portal/logs/
du -sh /opt/sales-portal/db_dumps/
```

### Cron 작업 실행 이력 확인

```bash
# 시스템 로그에서 cron 작업 확인
grep CRON /var/log/cron
grep CRON /var/log/syslog

# 최근 cron 실행 이력 확인
grep "maintenance_batch.sh" /var/log/cron | tail -10
grep "backup_db.sh" /var/log/cron | tail -10
```

---

## 문제 해결

### 배치 작업이 실행되지 않는 경우

1. **Cron 작업 확인**:
   ```bash
   crontab -l
   ```

2. **스크립트 실행 권한 확인**:
   ```bash
   ls -l /opt/sales-portal/maintenance_batch.sh
   ls -l /opt/sales-portal/backup_db.sh
   
   # 실행 권한 부여 (필요시)
   chmod +x /opt/sales-portal/maintenance_batch.sh
   chmod +x /opt/sales-portal/backup_db.sh
   ```

3. **수동 실행 테스트**:
   ```bash
   /opt/sales-portal/maintenance_batch.sh
   ```

4. **로그 확인**:
   ```bash
   tail -f /opt/sales-portal/logs/maintenance.log
   ```

### 백업이 실패하는 경우

1. **디스크 공간 확인**:
   ```bash
   df -h /
   ```

2. **백업 디렉토리 권한 확인**:
   ```bash
   ls -ld /opt/sales-portal/db_dumps/
   ```

3. **데이터베이스 연결 확인**:
   ```bash
   cd /opt/sales-portal/backend
   source venv/bin/activate
   export DJANGO_SETTINGS_MODULE=settings.production
   export DB_NAME=192.168.99.37:1521/XEPDB1
   export DB_USER=salesportal
   export DB_PASSWORD=salesportal123
   
   python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1 FROM DUAL'); print('DB 연결 성공')"
   ```

### 로그 로테이션이 작동하지 않는 경우

1. **설정 파일 확인**:
   ```bash
   cat /etc/logrotate.d/sales-portal
   ```

2. **수동 로그 로테이션 테스트**:
   ```bash
   sudo logrotate -d /etc/logrotate.d/sales-portal
   sudo logrotate -f /etc/logrotate.d/sales-portal
   ```

3. **logrotate 로그 확인**:
   ```bash
   grep sales-portal /var/log/cron
   ```

### 디스크 공간 부족 경고가 발생하는 경우

1. **오래된 백업 파일 삭제**:
   ```bash
   # 30일 이상 된 백업 파일 확인
   find /opt/sales-portal/db_dumps/ -name "db_dump_*.json*" -mtime +30 -ls
   
   # 삭제 (주의!)
   find /opt/sales-portal/db_dumps/ -name "db_dump_*.json*" -mtime +30 -delete
   ```

2. **오래된 로그 파일 삭제**:
   ```bash
   # 30일 이상 된 로그 파일 확인
   find /opt/sales-portal/logs/ -name "*.log*" -mtime +30 -ls
   
   # 삭제 (주의!)
   find /opt/sales-portal/logs/ -name "*.log*" -mtime +30 -delete
   ```

3. **Python 캐시 파일 정리**:
   ```bash
   find /opt/sales-portal/ -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
   find /opt/sales-portal/ -name "*.pyc" -delete
   ```

---

## 추가 참고 사항

### 환경 변수

배치 작업 스크립트는 다음 환경 변수를 사용합니다:

- `DJANGO_SETTINGS_MODULE`: `settings.production`
- `DB_NAME`: `192.168.99.37:1521/XEPDB1`
- `DB_USER`: `salesportal`
- `DB_PASSWORD`: `salesportal123`
- `ORACLE_HOME`: `/u01/app/oracle/product/19c/db_1`

### 권한

- 모든 스크립트는 `adm1003701` 사용자 권한으로 실행됩니다.
- 로그 파일은 `adm1003701:adm1003701` 소유권으로 생성됩니다.

### 백업 파일 복원

백업 파일을 복원하려면:

```bash
cd /opt/sales-portal
./import_db.sh db_dumps/db_dump_YYYYMMDD_HHMMSS.json
```

자세한 내용은 `import_db.sh` 스크립트를 참조하세요.

---

## 문의 및 지원

운영 관련 문의사항이 있으시면 시스템 관리자에게 문의하세요.

