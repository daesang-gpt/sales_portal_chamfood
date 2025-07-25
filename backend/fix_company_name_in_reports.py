import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import Report, Company

def fix_company_names():
    # company 필드가 C로 시작하는(회사코드) Report만 필터링
    reports = Report.objects.filter(company__regex=r'^C\d{7}$')
    print(f"수정 대상 일지 개수: {reports.count()}")

    for report in reports:
        # company_obj가 연결되어 있으면 그 회사명으로 변경
        if report.company_obj:
            company_name = report.company_obj.company_name
        else:
            # company 필드(회사코드)로 Company 객체를 찾음
            company = Company.objects.filter(sales_diary_company_code=report.company).first()
            company_name = company.company_name if company else None

        if company_name:
            print(f"{report.id}: {report.company} → {company_name}")
            report.company = company_name
            report.save()
        else:
            print(f"{report.id}: {report.company} → 회사명 찾기 실패")

if __name__ == "__main__":
    fix_company_names() 