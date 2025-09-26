#!/bin/bash

# chart.tsx map 함수 타입 오류 수정

echo "=== Chart.tsx map 함수 타입 오류 수정 ==="

cd /opt/sales-portal/frontend

# 백업 생성
cp components/ui/chart.tsx components/ui/chart.tsx.backup.$(date +%Y%m%d_%H%M%S)

echo "map 함수 타입 오류 수정 중..."

# payload.map 함수의 매개변수에 타입 지정
sed -i 's/payload\.map((item, index) =>/payload.map((item: any, index: number) =>/g' components/ui/chart.tsx

echo "수정 완료!"

# 수정 확인
echo "=== 수정된 map 함수 ==="
grep -n "payload.map" components/ui/chart.tsx

echo "=== 빌드 테스트 시작 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 빌드 성공! 모든 TypeScript 오류 해결됨!"
else
    echo "❌ 빌드 실패. 추가 오류 확인 필요"
    echo "현재 오류:"
    npm run build 2>&1 | grep "Type error"
fi
