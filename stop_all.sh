#!/bin/bash

# 백엔드와 프론트엔드를 모두 중지하는 스크립트

PROJECT_ROOT="/opt/sales-portal"
cd "$PROJECT_ROOT"

echo "========================================"
echo "백엔드 및 프론트엔드 중지"
echo "========================================"
echo ""

# Backend 중지
echo "[1/2] Backend 중지 중..."
./stop_backend.sh

echo ""

# Frontend 중지
echo "[2/2] Frontend 중지 중..."
./stop_frontend.sh

echo ""
echo "========================================"
echo "✅ 모든 서버가 중지되었습니다!"
echo "========================================"

