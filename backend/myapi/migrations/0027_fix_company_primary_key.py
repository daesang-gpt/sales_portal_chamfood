# Generated migration to fix Company.company_code constraint
from django.db import migrations


def add_unique_if_not_exists(apps, schema_editor):
    """COMPANY_CODE에 UNIQUE가 없을 때만 추가 (이미 PK면 스킵)"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM user_constraints
            WHERE table_name = 'COMPANIES' AND constraint_type IN ('P', 'U')
            AND constraint_name IN (
                SELECT constraint_name FROM user_cons_columns
                WHERE table_name = 'COMPANIES' AND column_name = 'COMPANY_CODE'
            )
        """)
        if cursor.fetchone()[0] > 0:
            return  # 이미 PK 또는 UNIQUE가 있음
        cursor.execute('ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_UNIQUE" UNIQUE ("COMPANY_CODE")')


def reverse_noop(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        try:
            cursor.execute('ALTER TABLE "COMPANIES" DROP CONSTRAINT "COMPANIES_COMPANY_CODE_UNIQUE"')
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0026_fix_company_financial_status_company_code_type'),
    ]

    operations = [
        migrations.RunPython(add_unique_if_not_exists, reverse_noop),
    ]
