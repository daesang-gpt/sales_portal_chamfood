#!/bin/bash

# company-search-input.tsx useRef 타입 오류 수정

echo "=== Company Search Input useRef 타입 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/company-search-input.tsx components/ui/company-search-input.tsx.backup.$(date +%Y%m%d_%H%M%S)

echo "useRef 타입 오류 수정 중..."

# useRef<NodeJS.Timeout>() → useRef<NodeJS.Timeout | null>(null)
sed -i 's/useRef<NodeJS\.Timeout>()/useRef<NodeJS.Timeout | null>(null)/g' components/ui/company-search-input.tsx

echo "수정 완료!"

# 수정 확인
echo "=== 수정된 useRef 라인 ==="
grep -n "debounceTimeoutRef" components/ui/company-search-input.tsx

echo "=== 빌드 테스트 시작 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend 빌드 완전 성공!"
    echo "🎉 모든 TypeScript 오류 해결됨!"
    echo "📦 정적 페이지 생성 완료!"
else
    echo "❌ 빌드 실패. 추가 오류:"
    npm run build 2>&1 | grep -A 3 "Type error"
fi
