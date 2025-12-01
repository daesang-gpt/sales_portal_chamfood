# 운영 서버 DB 다운로드 스크립트
# 사용법: .\download_production_db.ps1
#
# 사전 요구사항:
# 1. SSH 클라이언트 설치 (Windows 10/11에는 기본 포함)
# 2. 운영 서버 SSH 접근 권한
# 3. 서버에 backup_db.sh 스크립트가 있어야 함

param(
    [switch]$SkipBackup,  # 기존 백업 파일만 다운로드
    [string]$FileName = ""  # 특정 파일명 지정 (예: db_dump_20251201_103420.json.gz)
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "운영 서버 DB 다운로드 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 서버 정보
$SERVER_IP = "192.168.99.37"
$SERVER_USER = "adm1003701"
$PROJECT_PATH = "/opt/sales-portal"
$BACKUP_DIR = "$PROJECT_PATH/db_dumps"

# 로컬 다운로드 디렉토리
$LOCAL_DOWNLOAD_DIR = ".\db_dumps"
if (-not (Test-Path $LOCAL_DOWNLOAD_DIR)) {
    New-Item -ItemType Directory -Path $LOCAL_DOWNLOAD_DIR | Out-Null
    Write-Host "✅ 로컬 다운로드 디렉토리 생성: $LOCAL_DOWNLOAD_DIR" -ForegroundColor Green
}

$backupFile = ""

# 특정 파일명이 지정된 경우
if ($FileName -ne "") {
    $backupFile = "$BACKUP_DIR/$FileName"
    Write-Host "[1/4] 지정된 파일 다운로드: $FileName" -ForegroundColor Yellow
    
    # 파일 존재 확인
    $checkCommand = "test -f `"$backupFile`" && echo 'FILE_EXISTS' || echo 'FILE_NOT_FOUND'"
    $checkResult = ssh "${SERVER_USER}@${SERVER_IP}" $checkCommand 2>&1
    
    if ($checkResult -notmatch "FILE_EXISTS") {
        Write-Host "❌ 지정된 파일을 찾을 수 없습니다: $backupFile" -ForegroundColor Red
        Write-Host "서버의 백업 파일 목록을 확인하세요:" -ForegroundColor Yellow
        ssh "${SERVER_USER}@${SERVER_IP}" "ls -lh $BACKUP_DIR/" 2>&1
        exit 1
    }
    
    Write-Host "✅ 파일 확인 완료: $backupFile" -ForegroundColor Green
    Write-Host ""
} elseif (-not $SkipBackup) {
    Write-Host "[1/4] 운영 서버에서 DB 백업 실행 중..." -ForegroundColor Yellow
    
    # SSH로 서버에 접속하여 백업 실행
    $sshCommand = @"
cd $PROJECT_PATH
if [ ! -f backup_db.sh ]; then
    echo "❌ backup_db.sh 파일을 찾을 수 없습니다: $PROJECT_PATH/backup_db.sh"
    exit 1
fi

chmod +x backup_db.sh
echo "========================================"
echo "운영 DB 백업 실행 중..."
echo "========================================"
./backup_db.sh

if [ `$? -eq 0 ]; then
    echo "✅ 백업 완료"
    # 가장 최근 백업 파일 찾기 (압축 파일 우선, 없으면 JSON 파일)
    LATEST_BACKUP=`$(ls -t `$BACKUP_DIR/db_dump_*.json.gz 2>/dev/null | head -1)
    if [ -z "`$LATEST_BACKUP" ]; then
        LATEST_BACKUP=`$(ls -t `$BACKUP_DIR/db_dump_*.json 2>/dev/null | head -1)
    fi
    if [ -n "`$LATEST_BACKUP" ]; then
        echo "BACKUP_FILE:`$LATEST_BACKUP"
    else
        echo "❌ 백업 파일을 찾을 수 없습니다."
        exit 1
    fi
else
    echo "❌ 백업 실패"
    exit 1
fi
"@

    $backupResult = ssh "${SERVER_USER}@${SERVER_IP}" $sshCommand 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 백업 실행 실패" -ForegroundColor Red
        Write-Host "에러 메시지:" -ForegroundColor Yellow
        Write-Host $backupResult
        Write-Host ""
        Write-Host "참고: SSH 접속이 안 되는 경우 다음을 확인하세요:" -ForegroundColor Yellow
        Write-Host "  1. 서버 IP와 사용자명이 올바른지 확인" -ForegroundColor Gray
        Write-Host "  2. SSH 키 또는 비밀번호 설정 확인" -ForegroundColor Gray
        Write-Host "  3. 네트워크 연결 확인" -ForegroundColor Gray
        exit 1
    }

    # 백업 파일 경로 추출
    foreach ($line in $backupResult) {
        if ($line -match "BACKUP_FILE:(.+)") {
            $backupFile = $matches[1].Trim()
            break
        }
    }

    if ([string]::IsNullOrEmpty($backupFile)) {
        Write-Host "❌ 백업 파일 경로를 찾을 수 없습니다." -ForegroundColor Red
        Write-Host "백업 결과:" -ForegroundColor Yellow
        Write-Host $backupResult
        exit 1
    }

    Write-Host "✅ 백업 파일 생성 완료: $backupFile" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/4] 기존 백업 파일 찾기 중..." -ForegroundColor Yellow
    
    # 서버에서 가장 최근 백업 파일 찾기
    $findCommand = @"
LATEST_BACKUP=`$(ls -t $BACKUP_DIR/db_dump_*.json.gz 2>/dev/null | head -1)
if [ -z "`$LATEST_BACKUP" ]; then
    LATEST_BACKUP=`$(ls -t $BACKUP_DIR/db_dump_*.json 2>/dev/null | head -1)
fi
if [ -n "`$LATEST_BACKUP" ]; then
    echo "BACKUP_FILE:`$LATEST_BACKUP"
else
    echo "❌ 백업 파일을 찾을 수 없습니다."
    exit 1
fi
"@
    
    $findResult = ssh "${SERVER_USER}@${SERVER_IP}" $findCommand 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 백업 파일 찾기 실패" -ForegroundColor Red
        Write-Host $findResult
        exit 1
    }
    
    foreach ($line in $findResult) {
        if ($line -match "BACKUP_FILE:(.+)") {
            $backupFile = $matches[1].Trim()
            break
        }
    }
    
    if ([string]::IsNullOrEmpty($backupFile)) {
        Write-Host "❌ 백업 파일을 찾을 수 없습니다." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ 백업 파일 발견: $backupFile" -ForegroundColor Green
    Write-Host ""
}

# 파일명 추출
if ($FileName -ne "") {
    $fileName = $FileName
} else {
    $fileName = Split-Path $backupFile -Leaf
}

$stepNum = if ($FileName -ne "") { "[2/4]" } else { "[2/4]" }
Write-Host "$stepNum 백업 파일 다운로드 중..." -ForegroundColor Yellow
Write-Host "원본: ${SERVER_USER}@${SERVER_IP}:$backupFile" -ForegroundColor Gray
Write-Host "대상: $LOCAL_DOWNLOAD_DIR\$fileName" -ForegroundColor Gray

# SCP로 파일 다운로드
scp "${SERVER_USER}@${SERVER_IP}:$backupFile" "$LOCAL_DOWNLOAD_DIR\$fileName" 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 파일 다운로드 실패" -ForegroundColor Red
    Write-Host "참고: SCP 접속이 안 되는 경우 다음을 확인하세요:" -ForegroundColor Yellow
    Write-Host "  1. SSH 키 또는 비밀번호 설정 확인" -ForegroundColor Gray
    Write-Host "  2. 파일 경로와 권한 확인" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ 파일 다운로드 완료: $LOCAL_DOWNLOAD_DIR\$fileName" -ForegroundColor Green

# 파일 크기 확인
$fileInfo = Get-Item "$LOCAL_DOWNLOAD_DIR\$fileName"
$fileSize = [math]::Round($fileInfo.Length / 1MB, 2)
Write-Host "파일 크기: $fileSize MB" -ForegroundColor Cyan

# 압축 파일인 경우 압축 해제 안내
if ($fileName -match "\.gz$") {
    Write-Host ""
    Write-Host "[3/4] 압축 해제 중..." -ForegroundColor Yellow
    $uncompressedFile = $fileName -replace "\.gz$", ""
    
    # PowerShell에서 gzip 압축 해제
    $inputStream = [System.IO.File]::OpenRead("$LOCAL_DOWNLOAD_DIR\$fileName")
    $gzipStream = New-Object System.IO.Compression.GzipStream($inputStream, [System.IO.Compression.CompressionMode]::Decompress)
    $outputStream = [System.IO.File]::Create("$LOCAL_DOWNLOAD_DIR\$uncompressedFile")
    $gzipStream.CopyTo($outputStream)
    $outputStream.Close()
    $gzipStream.Close()
    $inputStream.Close()
    
    $uncompressedInfo = Get-Item "$LOCAL_DOWNLOAD_DIR\$uncompressedFile"
    $uncompressedSize = [math]::Round($uncompressedInfo.Length / 1MB, 2)
    Write-Host "✅ 압축 해제 완료: $uncompressedFile ($uncompressedSize MB)" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 운영 서버 DB 다운로드 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "다운로드 위치: $LOCAL_DOWNLOAD_DIR\$fileName" -ForegroundColor Yellow
if ($fileName -match "\.gz$") {
    Write-Host "압축 해제 파일: $LOCAL_DOWNLOAD_DIR\$uncompressedFile" -ForegroundColor Yellow
}
Write-Host ""

