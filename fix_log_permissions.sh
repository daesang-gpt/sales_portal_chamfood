#!/bin/bash

# 로그 파일 권한 수정 및 확인 스크립트
# 사용법: ./fix_log_permissions.sh

PROJECT_ROOT="/opt/sales-portal"
LOG_DIR="$PROJECT_ROOT/logs"

echo "========================================"
echo "로그 파일 권한 수정"
echo "========================================"
echo ""

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 로그 디렉토리 권한 설정
chmod 755 "$LOG_DIR"
chown root:root "$LOG_DIR" 2>/dev/null || echo "⚠️  소유자 변경 실패 (정상일 수 있음)"

# 기존 로그 파일 권한 수정
if [ -f "$LOG_DIR/backend.log" ]; then
    chmod 644 "$LOG_DIR/backend.log"
    chown root:root "$LOG_DIR/backend.log" 2>/dev/null || echo "⚠️  backend.log 소유자 변경 실패"
    echo "✅ backend.log 권한 수정 완료"
else
    echo "ℹ️  backend.log 파일이 없습니다 (서버 시작 후 생성됨)"
fi

if [ -f "$LOG_DIR/frontend.log" ]; then
    chmod 644 "$LOG_DIR/frontend.log"
    chown root:root "$LOG_DIR/frontend.log" 2>/dev/null || echo "⚠️  frontend.log 소유자 변경 실패"
    echo "✅ frontend.log 권한 수정 완료"
else
    echo "ℹ️  frontend.log 파일이 없습니다 (서버 시작 후 생성됨)"
fi

# PID 파일 권한 수정
if [ -f "$LOG_DIR/backend.pid" ]; then
    chmod 644 "$LOG_DIR/backend.pid"
    echo "✅ backend.pid 권한 수정 완료"
fi

if [ -f "$LOG_DIR/frontend.pid" ]; then
    chmod 644 "$LOG_DIR/frontend.pid"
    echo "✅ frontend.pid 권한 수정 완료"
fi

echo ""
echo "========================================"
echo "로그 파일 확인 방법"
echo "========================================"
echo ""
echo "로그 파일을 확인하려면 다음 명령어를 사용하세요:"
echo ""
echo "  # Backend 로그 실시간 확인"
echo "  tail -f $LOG_DIR/backend.log"
echo ""
echo "  # Backend 로그 최근 50줄"
echo "  tail -n 50 $LOG_DIR/backend.log"
echo ""
echo "  # 에러만 확인"
echo "  grep -i error $LOG_DIR/backend.log | tail -20"
echo ""
echo "  # Frontend 로그 확인"
echo "  tail -f $LOG_DIR/frontend.log"
echo ""

