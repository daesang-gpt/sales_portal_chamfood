# Generated manually - Add missing company fields

from django.db import migrations, models


def add_missing_fields(apps, schema_editor):
    """필요한 필드가 없으면 추가"""
    with schema_editor.connection.cursor() as cursor:
        # 추가해야 할 필드 목록
        fields_to_add = [
            ('TAX_ID', 'VARCHAR2(50)', '사업자등록번호'),
            ('PROCESSING_ADDRESS', 'VARCHAR2(500)', '공장 주소'),
            ('SAP_CODE_TYPE', 'VARCHAR2(50)', 'SAP코드여부'),
            ('BIZ_CODE', 'VARCHAR2(50)', '사업'),
            ('BIZ_NAME', 'VARCHAR2(200)', '사업부'),
            ('DEPARTMENT_CODE', 'VARCHAR2(50)', '지점/팀'),
            ('DEPARTMENT', 'VARCHAR2(100)', '팀명'),
            ('EMPLOYEE_NUMBER', 'VARCHAR2(50)', '사원번호'),
            ('EMPLOYEE_NAME', 'VARCHAR2(100)', '영업 사원'),
            ('DISTRIBUTION_TYPE_SAP_CODE', 'VARCHAR2(50)', '유통형태코드'),
            ('CODE_CREATE_DATE', 'DATE', '코드생성일'),
            ('COMPANY_CODE', 'VARCHAR2(50)', '회사코드'),
        ]
        
        for field_name, field_type, comment in fields_to_add:
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_tab_columns 
                    WHERE table_name = 'COMPANIES' AND column_name = :col_name
                """, {'col_name': field_name})
                exists = cursor.fetchone()[0] > 0
                if not exists:
                    if field_type == 'DATE':
                        cursor.execute(f'ALTER TABLE "COMPANIES" ADD "{field_name}" {field_type}')
                    else:
                        cursor.execute(f'ALTER TABLE "COMPANIES" ADD "{field_name}" {field_type} NULL')
                    if comment:
                        cursor.execute(f'COMMENT ON COLUMN "COMPANIES"."{field_name}" IS \'{comment}\'')
            except Exception as e:
                print(f"필드 {field_name} 추가 중 오류 (무시됨): {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0013_remove_company_company_code_sm_remove_company_id_and_more'),
    ]

    operations = [
        migrations.RunPython(
            add_missing_fields,
            reverse_code=migrations.RunPython.noop
        ),
        # Django 모델 상태도 업데이트 (RunPython에서 이미 추가되었으므로 존재 여부 확인 후만 추가)
        migrations.RunPython(
            lambda apps, schema_editor: None,  # 이미 RunPython에서 처리됨
            reverse_code=migrations.RunPython.noop
        ),
        # Django 마이그레이션 상태만 업데이트 (필드는 이미 존재)
        # 필드는 RunPython에서 이미 추가되었으므로 Django 마이그레이션 상태만 업데이트
        # 실제 필드는 존재하므로 separateDatabaseState와 separateState를 사용
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
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
            ]
        ),
    ]

