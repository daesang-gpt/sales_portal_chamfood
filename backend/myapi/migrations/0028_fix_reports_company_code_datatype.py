# Generated migration to create COMPANY_CODE field and cleanup
from django.db import migrations


def add_company_code_if_not_exists(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM user_tab_columns
            WHERE table_name = 'REPORTS' AND column_name = 'COMPANY_CODE'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute('ALTER TABLE "REPORTS" ADD "COMPANY_CODE" NVARCHAR2(50) NULL')
        cursor.execute("""
            SELECT COUNT(*) FROM user_constraints
            WHERE table_name = 'REPORTS' AND constraint_type = 'R'
            AND constraint_name = 'REPORTS_COMPANY_CODE_FK'
        """)
        if cursor.fetchone()[0] == 0:
            # COMPANY_CODE 컬럼에 FK가 이미 있는지 확인 (다른 이름일 수 있음)
            cursor.execute("""
                SELECT COUNT(*) FROM user_constraints c
                INNER JOIN user_cons_columns u ON c.constraint_name = u.constraint_name
                WHERE c.table_name = 'REPORTS' AND c.constraint_type = 'R'
                AND u.column_name = 'COMPANY_CODE'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE "REPORTS" ADD CONSTRAINT "REPORTS_COMPANY_CODE_FK"
                    FOREIGN KEY ("COMPANY_CODE") REFERENCES "COMPANIES"("COMPANY_CODE")
                    ON DELETE SET NULL
                """)


def reverse_noop(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute('ALTER TABLE "REPORTS" DROP CONSTRAINT "REPORTS_COMPANY_CODE_FK"')
            cursor.execute('ALTER TABLE "REPORTS" DROP COLUMN "COMPANY_CODE"')
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0027_fix_company_primary_key'),
    ]

    operations = [
        migrations.RunPython(add_company_code_if_not_exists, reverse_noop),
    ]
