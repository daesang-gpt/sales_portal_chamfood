#!/bin/bash

# chart.tsx ChartLegend Pick 타입 오류 수정

echo "=== Chart.tsx ChartLegend Pick 타입 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/chart.tsx components/ui/chart.tsx.backup.$(date +%Y%m%d_%H%M%S)

echo "ChartLegend Pick 타입 오류 수정 중..."

# Pick 타입을 직접 속성 정의로 변경
sed -i 's/Pick<RechartsPrimitive\.LegendProps, "payload" | "verticalAlign"> & {/{\n      payload?: any\n      verticalAlign?: any/g' components/ui/chart.tsx

echo "수정 완료!"

# 수정 확인
echo "=== 수정된 ChartLegend 타입 정의 ==="
grep -A 10 -B 5 "payload?: any" components/ui/chart.tsx | tail -10

echo "=== 빌드 테스트 시작 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 빌드 성공! 모든 TypeScript 오류 해결됨!"
else
    echo "❌ 빌드 실패. 추가 오류 확인 필요"
    echo "현재 오류:"
    npm run build 2>&1 | grep -A 3 "Type error"
fi
