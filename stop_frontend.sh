#!/bin/bash

# Frontend 중지 스크립트

PROJECT_ROOT="/opt/sales-portal"
PID_FILE="$PROJECT_ROOT/logs/frontend.pid"

echo "========================================"
echo "Next.js Frontend 중지 중..."
echo "========================================"

# PID 파일에서 읽기
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "PID $PID 프로세스 종료 중..."
        kill $PID
        sleep 2
        
        # 강제 종료가 필요한 경우
        if ps -p $PID > /dev/null 2>&1; then
            echo "강제 종료 중..."
            kill -9 $PID
        fi
        
        echo "✅ Frontend가 중지되었습니다."
    else
        echo "⚠️  PID $PID 프로세스가 실행 중이 아닙니다."
    fi
    rm -f "$PID_FILE"
else
    echo "⚠️  PID 파일을 찾을 수 없습니다: $PID_FILE"
fi

# 프로세스 이름으로도 확인 및 종료
NEXT_PIDS=$(pgrep -f "next start\|next-server" || true)
if [ -n "$NEXT_PIDS" ]; then
    echo "실행 중인 Frontend 프로세스 발견: $NEXT_PIDS"
    echo "$NEXT_PIDS" | xargs kill 2>/dev/null || true
    sleep 1
    echo "$NEXT_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ 모든 Frontend 프로세스가 중지되었습니다."
else
    echo "✅ 실행 중인 Frontend 프로세스가 없습니다."
fi

