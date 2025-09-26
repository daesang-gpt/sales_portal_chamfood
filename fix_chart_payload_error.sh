#!/bin/bash

# chart.tsx payload 오류 수정 스크립트

echo "=== Chart.tsx payload 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/chart.tsx components/ui/chart.tsx.backup.$(date +%Y%m%d_%H%M%S)

# payload 속성을 타입 정의에 추가
sed -i '/labelKey?: string/a\      payload?: any' components/ui/chart.tsx

echo "수정 완료!"

# 수정 확인
echo "수정된 타입 정의:"
grep -A 10 -B 5 "payload?: any" components/ui/chart.tsx

echo "=== 빌드 테스트 시작 ==="
npm run build
