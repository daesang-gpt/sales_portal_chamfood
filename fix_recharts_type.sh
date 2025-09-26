#!/bin/bash

# Recharts PieChart label 타입 오류 수정 스크립트

echo "=== Recharts 타입 오류 수정 ==="

cd /opt/sales-portal/frontend/app/analytics/

# 백업 생성
cp page.tsx page.tsx.backup.$(date +%Y%m%d_%H%M%S)

# 기존 label 라인을 찾아서 교체
sed -i '/label={({ name, percent }/,/}/ {
  /label={({ name, percent }/c\
                  label={(props: any) => {\
                    const { name, percent } = props;\
                    return `${name} ${(percent * 100).toFixed(0)}%`;\
                  }}
  /}/d
}' page.tsx

echo "수정 완료!"

# 수정된 내용 확인
echo "수정된 라인들:"
grep -A 4 -B 1 "label={(props: any)" page.tsx

echo "=== 빌드 테스트 시작 ==="
cd /opt/sales-portal/frontend
npm run build
