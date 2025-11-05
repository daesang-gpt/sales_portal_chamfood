#!/usr/bin/env python
"""회사코드 C0000546의 재무정보 DB 존재 여부 확인 스크립트"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django.setup()

from myapi.models import Company, CompanyFinancialStatus

company_code = 'C0000546'

print(f"\n{'='*60}")
print(f"회사코드: {company_code}")
print(f"{'='*60}\n")

# 1. Company 테이블에서 회사 존재 여부 확인
print("1. COMPANIES 테이블 확인:")
try:
    company = Company.objects.get(company_code=company_code)
    print(f"   ✓ 회사 존재: {company.company_name}")
    print(f"   - 회사명: {company.company_name}")
    print(f"   - 회사코드: {company.company_code}")
    print(f"   - SAP코드: {company.company_code_sap or '(없음)'}")
except Company.DoesNotExist:
    print(f"   ✗ 회사가 COMPANIES 테이블에 존재하지 않습니다!")
    print(f"   → 재무정보를 로드하려면 먼저 회사 정보가 필요합니다.")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ 오류 발생: {e}")
    sys.exit(1)

# 2. CompanyFinancialStatus 테이블에서 재무정보 확인
print(f"\n2. COMPANY_FINANCIAL_STATUS 테이블 확인:")
# company 객체를 통해 조회 (Django ORM이 자동으로 JOIN 처리)
try:
    financial_statuses = list(company.financial_statuses.all().order_by('-fiscal_year'))
except Exception as e:
    print(f"   ✗ 조회 중 오류 발생: {e}")
    # 직접 SQL로 조회 시도
    from django.db import connection
    with connection.cursor() as cursor:
        try:
                # Oracle cx_Oracle 방식 시도
                try:
                    cx_cursor = cursor.cursor
                    cx_cursor.execute("""
                        SELECT CFS.FISCAL_YEAR, CFS.TOTAL_ASSETS, CFS.CAPITAL, CFS.TOTAL_EQUITY,
                               CFS.REVENUE, CFS.OPERATING_INCOME, CFS.NET_INCOME
                        FROM COMPANY_FINANCIAL_STATUS CFS
                        INNER JOIN COMPANIES C ON CFS.COMPANY_CODE = C.ID
                        WHERE C.COMPANY_CODE = :1
                        ORDER BY CFS.FISCAL_YEAR DESC
                    """, [company_code])
                    rows = cx_cursor.fetchall()
                    financial_statuses = rows
                except Exception:
                    # Django 방식 시도
                    cursor.execute("""
                        SELECT CFS.FISCAL_YEAR, CFS.TOTAL_ASSETS, CFS.CAPITAL, CFS.TOTAL_EQUITY,
                               CFS.REVENUE, CFS.OPERATING_INCOME, CFS.NET_INCOME
                        FROM COMPANY_FINANCIAL_STATUS CFS
                        INNER JOIN COMPANIES C ON CFS.COMPANY_CODE = C.ID
                        WHERE C.COMPANY_CODE = %s
                        ORDER BY CFS.FISCAL_YEAR DESC
                    """, [company_code])
                    rows = cursor.fetchall()
                    financial_statuses = rows
        except Exception as sql_error:
            print(f"   ✗ SQL 조회도 실패: {sql_error}")
            financial_statuses = []

if financial_statuses:
    print(f"   ✓ 재무정보 {len(financial_statuses)}건 발견:")
    print()
    for fs in financial_statuses:
        if isinstance(fs, tuple):  # SQL 결과인 경우
            fiscal_year, total_assets, capital, total_equity, revenue, operating_income, net_income = fs
            print(f"   - 결산년도: {fiscal_year}")
            print(f"     총자산: {total_assets:,}")
            print(f"     자본금: {capital:,}")
            print(f"     자본총계: {total_equity:,}")
            print(f"     매출액: {revenue:,}")
            print(f"     영업이익: {operating_income:,}")
            print(f"     당기순이익: {net_income:,}")
        else:  # Django 모델 객체인 경우
            print(f"   - 결산년도: {fs.fiscal_year}")
            print(f"     총자산: {fs.total_assets:,}")
            print(f"     자본금: {fs.capital:,}")
            print(f"     자본총계: {fs.total_equity:,}")
            print(f"     매출액: {fs.revenue:,}")
            print(f"     영업이익: {fs.operating_income:,}")
            print(f"     당기순이익: {fs.net_income:,}")
        print()
else:
    print(f"   ✗ 재무정보가 DB에 존재하지 않습니다!")
    print(f"   → company_financial.tsv 파일에는 데이터가 있지만,")
    print(f"     DB에 로드되지 않았을 수 있습니다.")
    print(f"\n   해결 방법:")
    print(f"   python manage.py upload_company_financial_tsv backend/company_financial.tsv")

print(f"\n{'='*60}")

