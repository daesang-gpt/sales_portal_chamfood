# 운영 서버 DB 다운로드 가이드

운영 서버에 있는 모든 데이터베이스 내용을 로컬로 다운로드하는 방법입니다.

## 사전 요구사항

1. **SSH 클라이언트**: Windows 10/11에는 기본 포함되어 있습니다.
2. **운영 서버 SSH 접근 권한**: 서버 계정 정보 필요
   - 서버 IP: `192.168.99.37`
   - 사용자명: `adm1003701`
   - 비밀번호: `dsit_459037&` (또는 SSH 키 설정)
3. **서버에 백업 스크립트 존재**: `/opt/sales-portal/backup_db.sh`

## 사용 방법

### 방법 1: 자동 백업 및 다운로드 (권장)

프로젝트 루트 디렉토리에서 PowerShell 스크립트를 실행합니다:

```powershell
.\download_production_db.ps1
```

이 스크립트는 다음 작업을 수행합니다:
1. 운영 서버에 SSH 접속
2. 서버에서 `backup_db.sh` 실행하여 DB 백업 생성
3. 생성된 백업 파일을 로컬 `db_dumps/` 디렉토리로 다운로드
4. 압축 파일인 경우 자동으로 압축 해제

### 방법 2: 기존 백업 파일만 다운로드

서버에 이미 백업 파일이 있는 경우, 백업을 다시 실행하지 않고 기존 파일만 다운로드:

```powershell
.\download_production_db.ps1 -SkipBackup
```

## 다운로드된 파일 위치

- **다운로드 디렉토리**: `db_dumps/`
- **파일명 형식**: `db_dump_YYYYMMDD_HHMMSS.json` 또는 `db_dump_YYYYMMDD_HHMMSS.json.gz`
- **파일 내용**: 모든 Django 모델 데이터 (User, Company, Report, CompanyFinancialStatus, SalesData)

## 백업 파일 형식

백업 파일은 JSON 형식으로 저장되며, 다음 모델들의 데이터를 포함합니다:
- `myapi.User` - 사용자 정보
- `myapi.Company` - 회사 정보
- `myapi.Report` - 영업일지
- `myapi.CompanyFinancialStatus` - 회사 재무상태
- `myapi.SalesData` - 매출정보

## 문제 해결

### SSH 접속 실패

**증상**: "Connection refused" 또는 "Permission denied" 오류

**해결 방법**:
1. 서버 IP와 사용자명이 올바른지 확인
2. 네트워크 연결 확인 (서버와 같은 네트워크에 있는지)
3. SSH 키 설정 확인 또는 비밀번호 입력

**SSH 키 설정 (선택사항)**:
```powershell
# SSH 키 생성 (처음 한 번만)
ssh-keygen -t rsa -b 4096

# 서버에 공개키 복사
ssh-copy-id adm1003701@192.168.99.37
```

### 백업 스크립트를 찾을 수 없음

**증상**: "backup_db.sh 파일을 찾을 수 없습니다" 오류

**해결 방법**:
1. 서버에 SSH 접속하여 파일 존재 확인:
   ```bash
   ssh adm1003701@192.168.99.37
   ls -la /opt/sales-portal/backup_db.sh
   ```
2. 파일이 없다면 서버에 배포 필요

### 파일 다운로드 실패

**증상**: SCP 다운로드 실패

**해결 방법**:
1. 서버의 백업 디렉토리 권한 확인
2. 디스크 공간 확인
3. 수동으로 파일 확인:
   ```bash
   ssh adm1003701@192.168.99.37 "ls -lh /opt/sales-portal/db_dumps/"
   ```

## 수동 다운로드 방법

자동 스크립트가 작동하지 않는 경우, 수동으로 다운로드할 수 있습니다:

### 1단계: 서버에서 백업 실행

```bash
ssh adm1003701@192.168.99.37
cd /opt/sales-portal
./backup_db.sh
```

### 2단계: 백업 파일 확인

```bash
ls -lh /opt/sales-portal/db_dumps/
```

### 3단계: 로컬로 파일 다운로드

```powershell
# PowerShell에서
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_YYYYMMDD_HHMMSS.json.gz .\db_dumps\
```

### 4단계: 압축 해제 (필요한 경우)

```powershell
# PowerShell에서 gzip 압축 해제
$inputStream = [System.IO.File]::OpenRead(".\db_dumps\db_dump_YYYYMMDD_HHMMSS.json.gz")
$gzipStream = New-Object System.IO.Compression.GzipStream($inputStream, [System.IO.Compression.CompressionMode]::Decompress)
$outputStream = [System.IO.File]::Create(".\db_dumps\db_dump_YYYYMMDD_HHMMSS.json")
$gzipStream.CopyTo($outputStream)
$outputStream.Close()
$gzipStream.Close()
$inputStream.Close()
```

## 백업 파일 사용

다운로드한 백업 파일은 다음 용도로 사용할 수 있습니다:

1. **로컬 개발 환경에 데이터 복원**: `import_db.sh` 또는 `import_db.bat` 사용
2. **데이터 분석**: JSON 파일을 직접 열어서 데이터 확인
3. **백업 보관**: 중요한 데이터의 백업 보관

## 주의사항

1. **데이터 크기**: 백업 파일이 클 수 있으므로 충분한 디스크 공간 확보
2. **네트워크 속도**: 대용량 파일 다운로드 시 시간이 걸릴 수 있음
3. **보안**: 백업 파일에는 민감한 정보가 포함될 수 있으므로 안전하게 보관
4. **정기 백업**: 운영 서버는 `backup_db.sh`가 cron으로 자동 실행되도록 설정 권장

## 관련 문서

- `DEPLOYMENT_GUIDE.md` - 서버 배포 가이드
- `backup_db.sh` - 서버 백업 스크립트
- `import_db.sh` - 데이터 복원 스크립트

