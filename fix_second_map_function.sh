#!/bin/bash

# chart.tsx 두 번째 map 함수 타입 오류 수정

echo "=== Chart.tsx 두 번째 map 함수 타입 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/chart.tsx components/ui/chart.tsx.backup.$(date +%Y%m%d_%H%M%S)

echo "모든 map 함수 타입 오류 수정 중..."

# 모든 payload.map 함수에서 타입이 누락된 item 매개변수 수정
sed -i 's/payload\.map((item) =>/payload.map((item: any) =>/g' components/ui/chart.tsx

echo "수정 완료!"

# 수정 확인
echo "=== 수정된 모든 map 함수들 ==="
grep -n "payload.map" components/ui/chart.tsx

echo "=== 빌드 테스트 시작 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 빌드 성공! 모든 TypeScript 오류 해결됨!"
    echo "🎉 Frontend 빌드 완료! 이제 Django 마이그레이션으로 넘어갈 수 있습니다."
else
    echo "❌ 빌드 실패. 추가 오류 확인:"
    npm run build 2>&1 | grep -A 2 "Type error" | head -10
fi
