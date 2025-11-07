#!/bin/bash

# 서버 실행 상태 확인 스크립트

PROJECT_ROOT="/opt/sales-portal"

echo "========================================"
echo "서버 실행 상태 확인"
echo "========================================"
echo ""

# Backend 상태 확인
echo "[Backend]"
BACKEND_PID=$(pgrep -f "manage.py runserver" || echo "")
if [ -n "$BACKEND_PID" ]; then
    echo "  상태: ✅ 실행 중"
    echo "  PID: $BACKEND_PID"
    
    # 포트 확인
    if netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
        echo "  포트 8000: ✅ 열림"
    else
        echo "  포트 8000: ⚠️  확인 불가"
    fi
    
    # 메모리 사용량
    if command -v ps >/dev/null 2>&1; then
        MEM=$(ps -p $BACKEND_PID -o rss= 2>/dev/null | awk '{printf "%.1f", $1/1024}')
        if [ -n "$MEM" ]; then
            echo "  메모리: ${MEM} MB"
        fi
    fi
else
    echo "  상태: ❌ 실행 중이 아님"
fi

echo ""

# Frontend 상태 확인
echo "[Frontend]"
FRONTEND_PID=$(pgrep -f "next start\|next-server\|next start -H" || echo "")
if [ -n "$FRONTEND_PID" ]; then
    echo "  상태: ✅ 실행 중"
    echo "  PID: $FRONTEND_PID"
    
    # 포트 확인
    if netstat -tuln 2>/dev/null | grep -q ":3000 " || ss -tuln 2>/dev/null | grep -q ":3000 "; then
        echo "  포트 3000: ✅ 열림"
    else
        echo "  포트 3000: ⚠️  확인 불가"
    fi
    
    # 메모리 사용량
    if command -v ps >/dev/null 2>&1; then
        MEM=$(ps -p $FRONTEND_PID -o rss= 2>/dev/null | awk '{printf "%.1f", $1/1024}')
        if [ -n "$MEM" ]; then
            echo "  메모리: ${MEM} MB"
        fi
    fi
else
    echo "  상태: ❌ 실행 중이 아님"
fi

echo ""
echo "========================================"
echo "로그 파일 위치:"
echo "  Backend:  $PROJECT_ROOT/logs/backend.log"
echo "  Frontend: $PROJECT_ROOT/logs/frontend.log"
echo "========================================"

