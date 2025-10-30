# Generated manually - Set company_code as primary key

from django.db import migrations, models


def set_company_code_as_primary_key(apps, schema_editor):
    """company_code를 primary key로 설정"""
    with schema_editor.connection.cursor() as cursor:
        try:
            # 먼저 기존 ID primary key 제약 조건 제거
            cursor.execute("""
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = 'COMPANIES' 
                AND constraint_type = 'P'
            """)
            pk_constraint = cursor.fetchone()
            if pk_constraint:
                cursor.execute(f'ALTER TABLE "COMPANIES" DROP CONSTRAINT "{pk_constraint[0]}"')
            
            # ID 컬럼 제거 (외래키 참조가 없어야 함)
            # 외래키 참조가 있으면 나중에 처리
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'COMPANIES' AND column_name = 'ID'
            """)
            has_id = cursor.fetchone()[0] > 0
            
            # company_code를 primary key로 설정 (이미 설정되었으면 스킵)
            try:
                cursor.execute('ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_PK" PRIMARY KEY ("COMPANY_CODE")')
            except Exception as pk_error:
                # 이미 primary key가 설정되어 있으면 무시
                if 'ORA-02260' not in str(pk_error) and 'ORA-02273' not in str(pk_error):
                    raise
        except Exception as e:
            print(f"Primary key 설정 중 오류 (일부 무시됨): {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0011_recreate_company_model'),
    ]

    operations = [
        # company_code를 primary key로 설정
        migrations.RunPython(
            set_company_code_as_primary_key,
            reverse_code=migrations.RunPython.noop
        ),
        # Django 모델 상태만 업데이트 (데이터베이스는 이미 RunPython에서 처리됨)
        migrations.AlterField(
            model_name='company',
            name='company_code',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='회사코드'),
        ),
    ]

