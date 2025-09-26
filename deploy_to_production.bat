@echo off
REM 운영서버 배포 스크립트 (Windows)
REM 사용법: deploy_to_production.bat

echo 🚀 운영서버 배포를 시작합니다...

REM 1. 현재 변경사항 커밋
echo 📝 변경사항을 커밋합니다...
git add .
git commit -m "Deploy to production - %date% %time%" || echo 커밋할 변경사항이 없습니다.

REM 2. GitHub에 푸시
echo 📤 GitHub에 푸시합니다...
git push origin main

REM 3. 운영서버에 푸시
echo 🌐 운영서버에 배포합니다...
git push production main

echo ✅ 배포가 완료되었습니다!
echo 🔗 운영서버에서 다음 명령어로 업데이트하세요:
echo    cd /var/www/sales-portal
echo    git pull origin main
echo    # 백엔드 재시작
echo    systemctl restart sales-portal-backend
echo    # 프론트엔드 빌드 및 재시작
echo    cd frontend ^&^& npm run build ^&^& systemctl restart sales-portal-frontend

pause
