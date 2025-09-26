#!/bin/bash

# chart.tsx 모든 누락된 속성 오류 일괄 수정

echo "=== Chart.tsx 모든 속성 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/chart.tsx components/ui/chart.tsx.backup.$(date +%Y%m%d_%H%M%S)

echo "현재 사용 중인 속성들 확인..."
grep -A 20 "active," components/ui/chart.tsx | head -15

echo "누락된 속성들 추가 중..."

# 모든 필요한 속성들을 타입 정의에 추가
sed -i '/payload?: any/a\      label?: any\n      labelFormatter?: any\n      labelClassName?: string\n      formatter?: any\n      color?: string' components/ui/chart.tsx

echo "수정 완료!"

# 수정 확인
echo "=== 수정된 타입 정의 ==="
grep -A 15 "payload?: any" components/ui/chart.tsx

echo "=== 빌드 테스트 시작 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 빌드 성공!"
else
    echo "❌ 빌드 실패. 추가 수정 필요"
    echo "현재 사용 중인 모든 속성들:"
    grep -A 20 "active," components/ui/chart.tsx | head -15
fi
