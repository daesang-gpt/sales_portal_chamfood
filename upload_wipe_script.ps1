# wipe_production_server.sh 파일을 서버로 업로드하는 스크립트

$SERVER_IP = "192.168.99.37"
$SERVER_USER = "adm1003701"
$REMOTE_PATH = "/opt/sales-portal"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "서버 삭제 스크립트 업로드" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 파일 존재 확인
if (-not (Test-Path "wipe_production_server.sh")) {
    Write-Host "❌ 오류: wipe_production_server.sh 파일을 찾을 수 없습니다." -ForegroundColor Red
    Write-Host "   현재 디렉토리: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/2] 파일 업로드 중..." -ForegroundColor Yellow
Write-Host "  로컬: wipe_production_server.sh" -ForegroundColor Gray
Write-Host "  서버: ${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/wipe_production_server.sh" -ForegroundColor Gray
Write-Host ""

# SCP로 파일 업로드
scp wipe_production_server.sh "${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 파일 업로드 완료!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[2/2] 실행 권한 부여 중..." -ForegroundColor Yellow
    
    # SSH로 실행 권한 부여
    ssh "${SERVER_USER}@${SERVER_IP}" "chmod +x ${REMOTE_PATH}/wipe_production_server.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 실행 권한 부여 완료!" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "✅ 업로드 완료!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "서버에서 실행 방법:" -ForegroundColor Yellow
        Write-Host "  ssh ${SERVER_USER}@${SERVER_IP}" -ForegroundColor Gray
        Write-Host "  cd ${REMOTE_PATH}" -ForegroundColor Gray
        Write-Host "  ./wipe_production_server.sh" -ForegroundColor Gray
    } else {
        Write-Host "❌ 실행 권한 부여 실패" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 파일 업로드 실패" -ForegroundColor Red
    Write-Host "수동 업로드 방법:" -ForegroundColor Yellow
    Write-Host "  scp wipe_production_server.sh ${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/" -ForegroundColor Gray
}

