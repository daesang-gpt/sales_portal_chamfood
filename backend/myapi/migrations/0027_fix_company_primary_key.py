# Generated migration to fix Company.company_code constraint
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0026_fix_company_financial_status_company_code_type'),
    ]

    operations = [
        # Company 테이블의 company_code에 UNIQUE 제약조건 추가
        migrations.RunSQL(
            # Forward SQL - UNIQUE 제약조건 추가
            sql="""
                ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_UNIQUE" UNIQUE ("COMPANY_CODE")
            """,
            # Reverse SQL - UNIQUE 제약조건 제거
            reverse_sql="""
                ALTER TABLE "COMPANIES" DROP CONSTRAINT "COMPANIES_COMPANY_CODE_UNIQUE"
            """
        ),
    ]
