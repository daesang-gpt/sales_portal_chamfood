#!/bin/bash

# Backend 중지 스크립트

PROJECT_ROOT="/opt/sales-portal"
PID_FILE="$PROJECT_ROOT/logs/backend.pid"

echo "========================================"
echo "Django Backend 중지 중..."
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
        
        echo "✅ Backend가 중지되었습니다."
    else
        echo "⚠️  PID $PID 프로세스가 실행 중이 아닙니다."
    fi
    rm -f "$PID_FILE"
else
    echo "⚠️  PID 파일을 찾을 수 없습니다: $PID_FILE"
fi

# 프로세스 이름으로도 확인 및 종료
RUNSERVER_PIDS=$(pgrep -f "manage.py runserver" || true)
if [ -n "$RUNSERVER_PIDS" ]; then
    echo "실행 중인 Backend 프로세스 발견: $RUNSERVER_PIDS"
    echo "$RUNSERVER_PIDS" | xargs kill 2>/dev/null || true
    sleep 1
    echo "$RUNSERVER_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ 모든 Backend 프로세스가 중지되었습니다."
else
    echo "✅ 실행 중인 Backend 프로세스가 없습니다."
fi

