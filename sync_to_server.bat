@echo off
echo === 서버 동기화 시작 ===

REM 1. Git에 변경사항 커밋
git add .
git commit -m "Update: %date% %time%"
git push origin main

REM 2. 서버에서 Git Pull 실행
ssh adm1003701@192.168.99.37 "cd /opt/sales-portal && git pull origin main"

echo === 서버 동기화 완료 ===
pause
