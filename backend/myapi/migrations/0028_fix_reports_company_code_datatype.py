# Generated migration to create COMPANY_CODE field and cleanup
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0027_fix_company_primary_key'),
    ]

    operations = [
        # REPORTS 테이블에 새로운 COMPANY_CODE 필드 생성 및 정리
        migrations.RunSQL(
            # Forward SQL
            sql="""
                ALTER TABLE "REPORTS" ADD "COMPANY_CODE" NVARCHAR2(50) NULL;
                
                ALTER TABLE "REPORTS" ADD CONSTRAINT "REPORTS_COMPANY_CODE_FK" 
                    FOREIGN KEY ("COMPANY_CODE") REFERENCES "COMPANIES"("COMPANY_CODE") 
                    ON DELETE SET NULL;
            """,
            # Reverse SQL
            reverse_sql="""
                ALTER TABLE "REPORTS" DROP CONSTRAINT "REPORTS_COMPANY_CODE_FK";
                ALTER TABLE "REPORTS" DROP COLUMN "COMPANY_CODE";
            """
        ),
    ]
