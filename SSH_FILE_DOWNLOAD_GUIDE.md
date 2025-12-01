# SSH 서버에서 파일 다운로드 가이드

SSH 서버에 있는 파일을 로컬 컴퓨터로 다운로드하는 여러 방법을 설명합니다.

## 방법 1: SCP (Secure Copy) 사용 (가장 일반적)

SCP는 SSH를 통해 파일을 안전하게 복사하는 명령어입니다.

### 기본 사용법

```bash
scp [사용자명]@[서버IP]:[서버파일경로] [로컬저장경로]
```

### 예제

**단일 파일 다운로드:**
```bash
# Linux/Mac/Git Bash
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./db_dumps/

# Windows PowerShell
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz .\db_dumps\
```

**여러 파일 다운로드 (와일드카드 사용):**
```bash
# 모든 JSON 파일 다운로드
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/*.json ./db_dumps/

# 특정 패턴의 파일 다운로드
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_*.json.gz ./db_dumps/
```

**디렉토리 전체 다운로드:**
```bash
# -r 옵션으로 재귀적 복사
scp -r adm1003701@192.168.99.37:/opt/sales-portal/db_dumps ./backup/
```

### SCP 옵션

```bash
# 포트 지정 (기본 22번이 아닌 경우)
scp -P 2222 adm1003701@192.168.99.37:/path/to/file ./

# 압축 전송 (대용량 파일)
scp -C adm1003701@192.168.99.37:/path/to/file ./

# 진행 상황 표시
scp -v adm1003701@192.168.99.37:/path/to/file ./

# 여러 옵션 조합
scp -C -v -P 2222 adm1003701@192.168.99.37:/path/to/file ./
```

## 방법 2: SFTP 사용

SFTP는 대화형으로 파일을 전송할 수 있는 프로토콜입니다.

### 기본 사용법

```bash
# SFTP 접속
sftp adm1003701@192.168.99.37

# SFTP 명령어
sftp> ls                    # 서버 파일 목록 보기
sftp> cd /opt/sales-portal  # 서버 디렉토리 이동
sftp> lcd ./db_dumps        # 로컬 디렉토리 변경
sftp> get db_dump_20251201_103420.json.gz  # 파일 다운로드
sftp> get -r db_dumps       # 디렉토리 전체 다운로드
sftp> mget *.json.gz        # 여러 파일 다운로드
sftp> bye                   # 종료
```

### SFTP 한 줄 명령어

```bash
# 파일 다운로드
sftp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./db_dumps/

# 여러 파일 다운로드
sftp adm1003701@192.168.99.37 <<EOF
cd /opt/sales-portal/db_dumps
lcd ./db_dumps
mget *.json.gz
bye
EOF
```

## 방법 3: rsync 사용 (동기화)

rsync는 파일 동기화에 유용하며, 변경된 부분만 전송하여 효율적입니다.

### 기본 사용법

```bash
# 파일 다운로드
rsync -avz adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./db_dumps/

# 디렉토리 동기화
rsync -avz adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/ ./db_dumps/

# 진행 상황 표시
rsync -avz --progress adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/*.json.gz ./db_dumps/
```

### rsync 옵션 설명

- `-a`: 아카이브 모드 (권한, 시간 등 보존)
- `-v`: 상세 출력
- `-z`: 압축 전송
- `--progress`: 진행 상황 표시
- `--delete`: 로컬에 없는 파일 삭제 (동기화)

## 방법 4: SSH + cat/redirect (작은 파일용)

작은 텍스트 파일의 경우 SSH로 직접 내용을 가져올 수 있습니다.

```bash
# JSON 파일 내용을 로컬 파일로 저장
ssh adm1003701@192.168.99.37 "cat /opt/sales-portal/db_dumps/db_dump_20251201_103420.json" > ./db_dumps/db_dump_20251201_103420.json
```

## Windows에서 사용하기

### PowerShell (Windows 10/11)

PowerShell에는 기본적으로 SSH/SCP가 포함되어 있습니다.

```powershell
# SCP 사용
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz .\db_dumps\

# SFTP 사용
sftp adm1003701@192.168.99.37
```

### Git Bash

Git Bash를 사용하면 Linux 명령어를 Windows에서 사용할 수 있습니다.

```bash
# Git Bash에서 실행
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./db_dumps/
```

### WinSCP (GUI 도구)

GUI를 선호하는 경우 WinSCP를 사용할 수 있습니다.

1. WinSCP 다운로드 및 설치: https://winscp.net/
2. 서버 정보 입력:
   - 호스트명: `192.168.99.37`
   - 사용자명: `adm1003701`
   - 비밀번호: `dsit_459037&`
3. 파일 탐색기처럼 드래그 앤 드롭으로 다운로드

## 인증 방법

### 비밀번호 인증

처음 접속 시 비밀번호를 입력합니다.

```bash
scp adm1003701@192.168.99.37:/path/to/file ./
# 비밀번호 입력 요청: dsit_459037&
```

### SSH 키 인증 (권장)

비밀번호 없이 접속하려면 SSH 키를 설정합니다.

```bash
# 1. SSH 키 생성 (로컬에서)
ssh-keygen -t rsa -b 4096

# 2. 공개키를 서버에 복사
ssh-copy-id adm1003701@192.168.99.37

# 또는 수동으로 복사
cat ~/.ssh/id_rsa.pub | ssh adm1003701@192.168.99.37 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# 3. 이후 비밀번호 없이 접속 가능
scp adm1003701@192.168.99.37:/path/to/file ./
```

## 실제 사용 예제

### 예제 1: 특정 JSON 파일 다운로드

```bash
# 서버에서 파일 확인
ssh adm1003701@192.168.99.37 "ls -lh /opt/sales-portal/db_dumps/"

# 파일 다운로드
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./db_dumps/
```

### 예제 2: 최신 백업 파일 다운로드

```bash
# 서버에서 가장 최근 파일 찾기
LATEST_FILE=$(ssh adm1003701@192.168.99.37 "ls -t /opt/sales-portal/db_dumps/db_dump_*.json.gz | head -1")

# 파일 다운로드
scp "adm1003701@192.168.99.37:$LATEST_FILE" ./db_dumps/
```

### 예제 3: 모든 백업 파일 다운로드

```bash
# 모든 JSON 파일 다운로드
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/*.json ./db_dumps/

# 압축 파일 포함
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/*.json* ./db_dumps/
```

### 예제 4: 압축 해제와 함께 다운로드

```bash
# 압축 파일 다운로드
scp adm1003701@192.168.99.37:/opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz ./

# 압축 해제
gunzip db_dump_20251201_103420.json.gz

# 또는 한 번에
ssh adm1003701@192.168.99.37 "cat /opt/sales-portal/db_dumps/db_dump_20251201_103420.json.gz | gunzip" > db_dump_20251201_103420.json
```

## 문제 해결

### "Permission denied" 오류

```bash
# 파일 권한 확인
ssh adm1003701@192.168.99.37 "ls -la /opt/sales-portal/db_dumps/"

# 권한이 없다면 서버 관리자에게 요청
```

### "Connection refused" 오류

```bash
# 서버 IP와 포트 확인
ping 192.168.99.37

# 포트가 다른 경우
scp -P 2222 adm1003701@192.168.99.37:/path/to/file ./
```

### 대용량 파일 다운로드 중단

```bash
# nohup으로 백그라운드 실행
nohup scp adm1003701@192.168.99.37:/path/to/large_file.json.gz ./ &

# 또는 tmux/screen 사용
tmux new -s download
scp adm1003701@192.168.99.37:/path/to/large_file.json.gz ./
# Ctrl+B, D로 detach
```

## 자동화 스크립트

프로젝트에 이미 자동화 스크립트가 있습니다:

- **PowerShell**: `.\download_production_db.ps1 -FileName "파일명"`
- **Bash**: `./download_production_db.sh --file 파일명`

자세한 내용은 `DB_DOWNLOAD_GUIDE.md`를 참고하세요.

