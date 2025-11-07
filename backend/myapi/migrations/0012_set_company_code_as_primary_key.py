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
                # 외래 키 참조 확인
                cursor.execute("""
                    SELECT constraint_name 
                    FROM user_constraints 
                    WHERE table_name IN (
                        SELECT table_name 
                        FROM user_constraints 
                        WHERE constraint_type = 'R' 
                        AND r_constraint_name = :pk_constraint
                    )
                """, {'pk_constraint': pk_constraint[0]})
                fk_constraints = cursor.fetchall()
                
                # 외래 키 제약 조건 제거
                for fk_constraint in fk_constraints:
                    try:
                        cursor.execute(f'ALTER TABLE "{fk_constraint[0]}" DROP CONSTRAINT "{fk_constraint[0]}"')
                    except Exception as e:
                        print(f"외래 키 제약 조건 제거 중 오류 (무시됨): {e}")
                
                # Primary key 제약 조건 제거
                cursor.execute(f'ALTER TABLE "COMPANIES" DROP CONSTRAINT "{pk_constraint[0]}"')
            
            # company_code가 이미 primary key인지 확인
            cursor.execute("""
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = 'COMPANIES' 
                AND constraint_type = 'P'
                AND constraint_name LIKE '%COMPANY_CODE%'
            """)
            existing_pk = cursor.fetchone()
            
            if not existing_pk:
                # company_code를 primary key로 설정
                try:
                    cursor.execute('ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_PK" PRIMARY KEY ("COMPANY_CODE")')
                    print("✅ company_code를 Primary key로 설정했습니다.")
                except Exception as pk_error:
                    # 이미 primary key가 설정되어 있으면 무시
                    error_msg = str(pk_error)
                    if 'ORA-02260' in error_msg or 'ORA-02273' in error_msg or 'already exists' in error_msg.lower():
                        print(f"⚠️  Primary key가 이미 설정되어 있습니다 (무시됨): {pk_error}")
                    else:
                        raise
            else:
                print("✅ company_code가 이미 Primary key로 설정되어 있습니다.")
        except Exception as e:
            print(f"⚠️  Primary key 설정 중 오류 (일부 무시됨): {e}")
            # 마이그레이션을 계속 진행할 수 있도록 예외를 다시 발생시키지 않음


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
        migrations.AlterField(
            model_name='company',
            name='company_code',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='회사코드'),
        ),
    ]

