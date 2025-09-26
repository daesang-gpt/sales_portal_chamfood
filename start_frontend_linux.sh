#!/bin/bash

# 운영서버용 Next.js Frontend 시작 스크립트

# 스크립트 실행 위치로 이동
cd /opt/sales-portal/frontend

echo "Next.js Frontend 시작 중..."
echo "서버 주소: http://192.168.99.37:3000"
echo "로그 파일: frontend.log"

# Next.js 서버 시작 (프로덕션 모드)
npm start
