# Generated manually - Set company_code as primary key

from django.db import migrations, models


def set_company_code_as_primary_key(apps, schema_editor):
    """company_code를 primary key로 설정"""
    with schema_editor.connection.cursor() as cursor:
        try:
            # 1. 먼저 company_code를 참조하는 모든 Foreign Key 제약조건 찾기 및 제거
            cursor.execute("""
                SELECT constraint_name, table_name 
                FROM user_constraints 
                WHERE constraint_type = 'R'
                AND r_constraint_name IN (
                    SELECT constraint_name 
                    FROM user_constraints 
                    WHERE table_name = 'COMPANIES' 
                    AND constraint_type IN ('P', 'U')
                )
            """)
            fk_constraints = cursor.fetchall()
            
            for fk_name, fk_table in fk_constraints:
                try:
                    cursor.execute(f'ALTER TABLE "{fk_table}" DROP CONSTRAINT "{fk_name}"')
                    print(f"  - Foreign Key 제약조건 제거: {fk_table}.{fk_name}")
                except Exception as e:
                    print(f"  ⚠️  Foreign Key 제약조건 제거 중 오류 (무시됨): {e}")
            
            # 2. 기존 ID primary key 제약 조건 제거
            cursor.execute("""
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = 'COMPANIES' 
                AND constraint_type = 'P'
            """)
            pk_constraint = cursor.fetchone()
            if pk_constraint:
                try:
                    cursor.execute(f'ALTER TABLE "COMPANIES" DROP CONSTRAINT "{pk_constraint[0]}" CASCADE')
                    print(f"  - 기존 Primary Key 제약조건 제거: {pk_constraint[0]}")
                except Exception as e:
                    print(f"  ⚠️  Primary Key 제약조건 제거 중 오류: {e}")
            
            # 3. ID 컬럼이 있으면 제거 (이미 제거되었을 수 있음)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'COMPANIES' AND column_name = 'ID'
            """)
            has_id = cursor.fetchone()[0] > 0
            if has_id:
                try:
                    cursor.execute('ALTER TABLE "COMPANIES" DROP COLUMN "ID"')
                    print("  - ID 컬럼 제거 완료")
                except Exception as e:
                    print(f"  ⚠️  ID 컬럼 제거 중 오류 (무시됨): {e}")
            
            # 4. company_code에 대한 기존 Unique 제약조건 찾기 및 제거
            cursor.execute("""
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = 'COMPANIES' 
                AND constraint_type = 'U'
                AND constraint_name IN (
                    SELECT constraint_name 
                    FROM user_cons_columns 
                    WHERE table_name = 'COMPANIES' 
                    AND column_name = 'COMPANY_CODE'
                )
            """)
            unique_constraints = cursor.fetchall()
            
            for constraint in unique_constraints:
                try:
                    cursor.execute(f'ALTER TABLE "COMPANIES" DROP CONSTRAINT "{constraint[0]}"')
                    print(f"  - Unique 제약조건 제거: {constraint[0]}")
                except Exception as e:
                    print(f"  ⚠️  Unique 제약조건 제거 중 오류 (무시됨): {e}")
            
            # 5. company_code가 이미 Primary Key인지 확인
            cursor.execute("""
                SELECT constraint_name 
                FROM user_constraints 
                WHERE table_name = 'COMPANIES' 
                AND constraint_type = 'P'
                AND constraint_name IN (
                    SELECT constraint_name 
                    FROM user_cons_columns 
                    WHERE table_name = 'COMPANIES' 
                    AND column_name = 'COMPANY_CODE'
                )
            """)
            existing_pk = cursor.fetchone()
            
            if existing_pk:
                print(f"  ℹ️  company_code가 이미 Primary Key로 설정되어 있습니다: {existing_pk[0]}")
            else:
                # 6. company_code를 primary key로 설정
                try:
                    cursor.execute('ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_PK" PRIMARY KEY ("COMPANY_CODE")')
                    print("  ✅ company_code를 Primary Key로 설정 완료")
                except Exception as pk_error:
                    error_str = str(pk_error)
                    if 'ORA-02260' in error_str:
                        # 이미 Primary Key가 존재 (다른 이름으로)
                        print("  ⚠️  이미 Primary Key가 존재합니다. 확인 중...")
                        cursor.execute("""
                            SELECT constraint_name 
                            FROM user_constraints 
                            WHERE table_name = 'COMPANIES' 
                            AND constraint_type = 'P'
                        """)
                        existing_pk = cursor.fetchone()
                        if existing_pk:
                            print(f"  ℹ️  기존 Primary Key: {existing_pk[0]}")
                        else:
                            raise
                    elif 'ORA-02261' in error_str:
                        # Unique 제약조건이 남아있음
                        print("  ⚠️  Unique 제약조건이 남아있습니다. 다시 제거 시도...")
                        # Unique 제약조건 다시 확인 및 제거
                        cursor.execute("""
                            SELECT constraint_name 
                            FROM user_constraints 
                            WHERE table_name = 'COMPANIES' 
                            AND constraint_type = 'U'
                            AND constraint_name IN (
                                SELECT constraint_name 
                                FROM user_cons_columns 
                                WHERE table_name = 'COMPANIES' 
                                AND column_name = 'COMPANY_CODE'
                            )
                        """)
                        remaining_unique = cursor.fetchall()
                        for constraint in remaining_unique:
                            try:
                                cursor.execute(f'ALTER TABLE "COMPANIES" DROP CONSTRAINT "{constraint[0]}"')
                                print(f"  - 남은 Unique 제약조건 제거: {constraint[0]}")
                            except:
                                pass
                        # 다시 Primary Key 설정 시도
                        try:
                            cursor.execute('ALTER TABLE "COMPANIES" ADD CONSTRAINT "COMPANIES_COMPANY_CODE_PK" PRIMARY KEY ("COMPANY_CODE")')
                            print("  ✅ company_code를 Primary Key로 설정 완료 (재시도 성공)")
                        except Exception as retry_error:
                            print(f"  ❌ Primary Key 설정 실패: {retry_error}")
                            raise
                    elif 'ORA-02273' in error_str:
                        print("  ⚠️  Foreign Key 참조가 있어 Primary Key 설정 실패")
                        raise
                    else:
                        print(f"  ❌ Primary Key 설정 중 예상치 못한 오류: {error_str}")
                        raise
                
                # 7. 최종 확인: Primary Key가 제대로 설정되었는지 확인
                cursor.execute("""
                    SELECT constraint_name 
                    FROM user_constraints 
                    WHERE table_name = 'COMPANIES' 
                    AND constraint_type = 'P'
                    AND constraint_name IN (
                        SELECT constraint_name 
                        FROM user_cons_columns 
                        WHERE table_name = 'COMPANIES' 
                        AND column_name = 'COMPANY_CODE'
                    )
                """)
                final_check = cursor.fetchone()
                if not final_check:
                    raise Exception("Primary Key 설정이 확인되지 않습니다!")
                print(f"  ✅ 최종 확인: Primary Key 설정됨 - {final_check[0]}")
                
        except Exception as e:
            error_str = str(e)
            print(f"❌ Primary key 설정 중 오류: {error_str}")
            # 치명적인 오류만 raise
            if 'ORA-02273' in error_str:
                raise Exception(f"Foreign Key 참조 문제로 Primary Key 설정 실패: {error_str}")
            elif 'ORA-02260' not in error_str and 'ORA-02261' not in error_str:
                # 예상치 못한 오류는 raise
                raise
            else:
                # 이미 설정되어 있을 수 있으므로 확인 후 진행
                print("  ⚠️  오류가 발생했지만 이미 설정되어 있을 수 있습니다. 확인 중...")
                cursor.execute("""
                    SELECT constraint_name 
                    FROM user_constraints 
                    WHERE table_name = 'COMPANIES' 
                    AND constraint_type = 'P'
                """)
                existing_pk = cursor.fetchone()
                if existing_pk:
                    print(f"  ℹ️  Primary Key가 존재합니다: {existing_pk[0]}")
                else:
                    raise Exception(f"Primary Key 설정 실패: {error_str}")


# 커스텀 AlterField 클래스: 실제 DB 변경을 스킵하고 모델 상태만 업데이트
class NoOpAlterField(migrations.AlterField):
    """DB 변경 없이 모델 상태만 업데이트하는 AlterField"""
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # DB 변경을 하지 않음 (RunPython에서 이미 처리됨)
        pass
    
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # DB 변경을 하지 않음
        pass


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
        # NoOpAlterField를 사용하여 실제 DB 변경을 스킵
        NoOpAlterField(
            model_name='company',
            name='company_code',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True, verbose_name='회사코드'),
        ),
    ]

