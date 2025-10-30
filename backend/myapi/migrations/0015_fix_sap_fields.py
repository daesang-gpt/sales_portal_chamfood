# Generated manually - Fix SAP fields to allow NULL

from django.db import migrations


def fix_sap_fields(apps, schema_editor):
    """SAP_HAS_PURCHASE, SAP_HAS_SALES 필드를 NULL 허용으로 변경하거나 삭제"""
    with schema_editor.connection.cursor() as cursor:
        # SAP_HAS_PURCHASE 필드 처리
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'COMPANIES' AND column_name = 'SAP_HAS_PURCHASE'
            """)
            has_sap_purchase = cursor.fetchone()[0] > 0
            if has_sap_purchase:
                # NULL 허용으로 변경
                cursor.execute('ALTER TABLE "COMPANIES" MODIFY "SAP_HAS_PURCHASE" NUMBER(1) NULL')
        except Exception as e:
            print(f"SAP_HAS_PURCHASE 처리 중 오류: {e}")
        
        # SAP_HAS_SALES 필드 처리
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'COMPANIES' AND column_name = 'SAP_HAS_SALES'
            """)
            has_sap_sales = cursor.fetchone()[0] > 0
            if has_sap_sales:
                # NULL 허용으로 변경
                cursor.execute('ALTER TABLE "COMPANIES" MODIFY "SAP_HAS_SALES" NUMBER(1) NULL')
        except Exception as e:
            print(f"SAP_HAS_SALES 처리 중 오류: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0014_add_missing_company_fields'),
    ]

    operations = [
        migrations.RunPython(
            fix_sap_fields,
            reverse_code=migrations.RunPython.noop
        ),
    ]

