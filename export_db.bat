@echo off
REM 개발 DB에서 데이터 덤프 생성 스크립트
REM 사용법: export_db.bat (프로젝트 루트에서 실행)

echo ========================================
echo 개발 DB 데이터 덤프 생성 시작
echo ========================================

REM 프로젝트 루트로 이동
cd /d %~dp0

REM 덤프 디렉토리 생성
if not exist db_dumps mkdir db_dumps

REM 타임스탬프 생성
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM 덤프 파일 경로
set DUMP_FILE=db_dumps\db_dump_%timestamp%.json

REM Backend 디렉토리로 이동
cd backend

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo 오류: 가상환경을 찾을 수 없습니다.
    echo 먼저 가상환경을 생성해주세요.
    pause
    exit /b 1
)

REM Django 환경변수 설정
set DJANGO_SETTINGS_MODULE=settings.development
set DB_NAME=localhost:1521/XEPDB1
set DB_USER=salesportal
set DB_PASSWORD=salesportal123
set SKIP_VIEWS_IMPORT=true
set PYTHONIOENCODING=utf-8

echo.
echo 데이터 덤프 생성 중...
echo 덤프 파일: ..\%DUMP_FILE%
echo.

REM Django dumpdata 실행 (UTF-8 인코딩 처리)
REM Python 스크립트를 사용하여 인코딩 문제 해결
python dump_db_utf8.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 데이터 덤프 생성 완료!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 오류: 데이터 덤프 생성 실패
    echo ========================================
    pause
    exit /b 1
)

pause
