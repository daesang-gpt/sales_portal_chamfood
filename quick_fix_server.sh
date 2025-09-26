#!/bin/bash

# 서버에서 직접 TypeScript 오류 수정하는 스크립트

echo "=== TypeScript 오류 자동 수정 ==="

cd /opt/sales-portal/frontend/app/analytics/

# 백업 생성
cp page.tsx page.tsx.backup.$(date +%Y%m%d_%H%M%S)

# 타입 오류 수정
sed -i 's/label={({ name, percent }) =>/label={({ name, percent }: { name: string; percent: number }) =>/g' page.tsx

# 수정 확인
echo "수정된 라인:"
grep -n "label.*percent.*name.*string" page.tsx

echo "=== 수정 완료 ==="

# 빌드 테스트
cd /opt/sales-portal/frontend
npm run build
