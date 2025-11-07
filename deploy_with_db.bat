@echo off
REM 개발서버에서 운영서버로 코드 및 DB 배포 스크립트 (Windows)
REM 사용법: deploy_with_db.bat

echo ========================================
echo 운영서버 배포 시작 (코드 + DB)
echo ========================================

REM 프로젝트 루트로 이동
cd /d %~dp0

REM 1. 데이터베이스 덤프 생성
echo.
echo [1/4] 개발 DB 데이터 덤프 생성 중...
call export_db.bat
if %ERRORLEVEL% NEQ 0 (
    echo 오류: DB 덤프 생성 실패
    pause
    exit /b 1
)

REM 최신 덤프 파일 찾기
for /f "delims=" %%I in ('dir /b /o-d db_dumps\db_dump_*.json 2^>nul') do (
    set LATEST_DUMP=%%I
    goto :found
)
:found

if not defined LATEST_DUMP (
    echo 오류: 덤프 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

echo 최신 덤프 파일: %LATEST_DUMP%

REM 2. Git에 변경사항 추가
echo.
echo [2/4] Git에 변경사항 추가 중...
git add .
git add db_dumps\%LATEST_DUMP%

REM 3. Git 커밋
echo.
echo [3/4] Git 커밋 중...
set COMMIT_MSG=Deploy to production with DB - %date% %time%
git commit -m "%COMMIT_MSG%" || (
    echo 경고: 커밋할 변경사항이 없거나 커밋 실패
)

REM 4. Git 푸시
echo.
echo [4/4] Git에 푸시 중...
echo GitHub에 푸시 중...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo 오류: GitHub 푸시 실패
    pause
    exit /b 1
)

REM 운영서버 remote가 설정되어 있으면 푸시
git remote show production >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 운영서버에 푸시 중...
    git push production main
)

echo.
echo ========================================
echo 배포 준비 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. 운영서버에 SSH 접속
echo 2. 다음 명령어 실행:
echo    cd /opt/sales-portal
echo    ./deploy_from_git_with_db.sh
echo.
echo 또는 운영서버에서 자동 배포 스크립트 실행:
echo    ssh adm1003701@192.168.99.37 "cd /opt/sales-portal && ./deploy_from_git_with_db.sh"
echo.

pause

