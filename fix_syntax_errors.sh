#!/bin/bash

# 구문 오류 수정 스크립트 - (data as any).(results as any) → (data as any).results

echo "=== 🔧 구문 오류 수정 시작 ==="

cd /opt/sales-portal/frontend

# 백업에서 복원
echo "백업에서 복원 중..."
cp -r /tmp/frontend_backup_20250923_101833/* ./

echo "=== 올바른 구문으로 수정 ==="

# 1. companies/[id]/page.tsx 수정
echo "companies/[id]/page.tsx 수정..."
sed -i '57s/.*/        const list = Array.isArray(data) ? data : (data as any).results;/' app/companies/\[id\]/page.tsx

# 2. companies/page.tsx 수정
echo "companies/page.tsx 수정..."
sed -i '49s/.*/      setCompanies((companiesData as any).results)/' app/companies/page.tsx
sed -i '83s/.*/        setCompanies((companiesData as any).results)/' app/companies/page.tsx

# 3. sales-reports/[id]/edit/page.tsx 수정
echo "sales-reports/[id]/edit/page.tsx 수정..."
sed -i '58s/.*/      setCompanies((data as any).results) \/\/ 반드시 (data as any).results로 배열만 저장/' app/sales-reports/\[id\]/edit/page.tsx

# 4. sales-reports/[id]/page.tsx 수정
echo "sales-reports/[id]/page.tsx 수정..."
sed -i '58s/.*/        setOtherReports((data as any).results)/' app/sales-reports/\[id\]/page.tsx

# 5. sales-reports/page.tsx 수정
echo "sales-reports/page.tsx 수정..."
sed -i '47s/.*/      setReports((data as any).results);/' app/sales-reports/page.tsx

# 6. chart.tsx 모든 map 함수 수정
echo "chart.tsx map 함수들 수정..."
sed -i 's/payload\.map((item) =>/payload.map((item: any) =>/g' components/ui/chart.tsx
sed -i 's/payload\.map((item, index) =>/payload.map((item: any, index: number) =>/g' components/ui/chart.tsx

# 7. company-search-input.tsx 수정
echo "company-search-input.tsx 수정..."
sed -i 's/useRef<NodeJS\.Timeout>()/useRef<NodeJS.Timeout | null>(null)/g' components/ui/company-search-input.tsx

echo "=== 수정 확인 ==="
echo "companies/[id]/page.tsx 57번째 줄:"
sed -n '57p' app/companies/\[id\]/page.tsx

echo "companies/page.tsx 49번째 줄:"
sed -n '49p' app/companies/page.tsx

echo "sales-reports/page.tsx 47번째 줄:"
sed -n '47p' app/sales-reports/page.tsx

echo "chart.tsx map 함수들:"
grep -n "payload.map" components/ui/chart.tsx

echo "=== 🚀 최종 빌드 테스트 ==="
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 🎉 모든 구문 오류 해결! 빌드 성공!"
    echo "🚀 Frontend 완전 준비 완료!"
else
    echo "❌ 빌드 실패. 남은 오류:"
    npm run build 2>&1 | grep -A 3 "Error:" | head -10
fi
