import csv
import os
import django
import sys

# Django 환경설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import Company, CompanyFinancialStatus, User

# Company 데이터 추출
company_fields = [
    'company_name', 'sales_diary_company_code', 'company_code_sm', 'company_code_sap', 'company_type',
    'established_date', 'ceo_name', 'address', 'contact_person', 'contact_phone', 'main_phone',
    'distribution_type_sap', 'industry_name', 'main_product', 'transaction_start_date', 'payment_terms',
    'customer_classification', 'website', 'remarks', 'username',
]

with open('companies_export.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(company_fields)
    for c in Company.objects.all():
        row = [
            c.company_name,
            c.sales_diary_company_code,
            c.company_code_sm,
            c.company_code_sap,
            c.company_type,
            c.established_date,
            c.ceo_name,
            c.address,
            c.contact_person,
            c.contact_phone,
            c.main_phone,
            c.distribution_type_sap,
            c.industry_name,
            c.main_product,
            c.transaction_start_date,
            c.payment_terms,
            c.customer_classification,
            c.website,
            c.remarks,
            c.username.username if c.username else '',
        ]
        writer.writerow(row)

# CompanyFinancialStatus 데이터 추출
cfs_fields = [
    'company', 'fiscal_year', 'total_assets', 'capital', 'total_equity', 'revenue', 'operating_income', 'net_income'
]

with open('company_financial_status_export.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(cfs_fields)
    for cfs in CompanyFinancialStatus.objects.all():
        row = [
            cfs.company.company_name if cfs.company else '',
            cfs.fiscal_year,
            cfs.total_assets,
            cfs.capital,
            cfs.total_equity,
            cfs.revenue,
            cfs.operating_income,
            cfs.net_income,
        ]
        writer.writerow(row) 