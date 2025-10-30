# Generated manually for Company model recreation

from django.db import migrations, models


def safe_remove_field(apps, schema_editor, model_name, field_name):
    """필드가 존재하는 경우에만 제거"""
    with schema_editor.connection.cursor() as cursor:
        try:
            # Oracle에서 컬럼 존재 여부 확인
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = :table_name AND column_name = :column_name
            """, {'table_name': model_name.upper(), 'column_name': field_name.upper()})
            exists = cursor.fetchone()[0] > 0
            if exists:
                cursor.execute(f'ALTER TABLE "{model_name.upper()}" DROP COLUMN "{field_name.upper()}"')
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0010_alter_company_products_alter_report_products'),
    ]

    operations = [
        # 기존 필드 제거 (존재하는 경우에만)
        migrations.RunPython(
            lambda apps, schema_editor: safe_remove_field(apps, schema_editor, 'COMPANIES', 'SALES_DIARY_COMPANY_CODE'),
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            lambda apps, schema_editor: safe_remove_field(apps, schema_editor, 'COMPANIES', 'COMPANY_CODE_SM'),
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            lambda apps, schema_editor: safe_remove_field(apps, schema_editor, 'COMPANIES', 'MAIN_PRODUCT'),
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            lambda apps, schema_editor: safe_remove_field(apps, schema_editor, 'COMPANIES', 'USERNAME_ID'),
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            lambda apps, schema_editor: safe_remove_field(apps, schema_editor, 'COMPANIES', 'LOCATION'),
            reverse_code=migrations.RunPython.noop
        ),
        
        # address를 head_address로 rename
        migrations.RenameField(
            model_name='company',
            old_name='address',
            new_name='head_address',
        ),
        
        # 새로운 필드들 추가
        migrations.AddField(
            model_name='company',
            name='tax_id',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='사업자등록번호'),
        ),
        migrations.AddField(
            model_name='company',
            name='processing_address',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='공장 주소'),
        ),
        migrations.AddField(
            model_name='company',
            name='sap_code_type',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='SAP코드여부'),
        ),
        migrations.AddField(
            model_name='company',
            name='biz_code',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='사업'),
        ),
        migrations.AddField(
            model_name='company',
            name='biz_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='사업부'),
        ),
        migrations.AddField(
            model_name='company',
            name='department_code',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='지점/팀'),
        ),
        migrations.AddField(
            model_name='company',
            name='department',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='팀명'),
        ),
        migrations.AddField(
            model_name='company',
            name='employee_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='사원번호'),
        ),
        migrations.AddField(
            model_name='company',
            name='employee_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='영업 사원'),
        ),
        migrations.AddField(
            model_name='company',
            name='distribution_type_sap_code',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='유통형태코드'),
        ),
        migrations.AddField(
            model_name='company',
            name='code_create_date',
            field=models.DateField(blank=True, null=True, verbose_name='코드생성일'),
        ),
        
        # company_code 필드 추가 (임시로 null=True)
        migrations.AddField(
            model_name='company',
            name='company_code',
            field=models.CharField(max_length=50, null=True, unique=True, verbose_name='회사코드'),
        ),
        
        # customer_classification choices 변경
        migrations.AlterField(
            model_name='company',
            name='customer_classification',
            field=models.CharField(blank=True, choices=[('기존', '기존'), ('신규', '신규'), ('이탈', '이탈'), ('기타', '기타')], max_length=50, null=True, verbose_name='고객분류'),
        ),
        
        # company_type choices 변경
        migrations.AlterField(
            model_name='company',
            name='company_type',
            field=models.CharField(blank=True, choices=[('개인', '개인'), ('법인', '법인')], max_length=50, null=True, verbose_name='회사유형'),
        ),
    ]

