from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'COMPANY_FINANCIAL_STATUS 테이블 구조를 확인합니다'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tables 
                WHERE table_name = 'COMPANY_FINANCIAL_STATUS'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                self.stdout.write(self.style.ERROR('테이블 COMPANY_FINANCIAL_STATUS가 존재하지 않습니다.'))
                return
            
            self.stdout.write(self.style.SUCCESS('테이블 COMPANY_FINANCIAL_STATUS 존재 확인됨'))
            self.stdout.write('='*60)
            
            # 컬럼 정보 조회
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale,
                    nullable,
                    data_default
                FROM user_tab_columns
                WHERE table_name = 'COMPANY_FINANCIAL_STATUS'
                ORDER BY column_id
            """)
            
            self.stdout.write('\n컬럼 정보:')
            self.stdout.write('-'*60)
            for row in cursor.fetchall():
                col_name, data_type, data_length, data_precision, data_scale, nullable, data_default = row
                scale_info = f", {data_scale}" if data_scale else ""
                precision_info = f"({data_precision}{scale_info})" if data_precision else f"({data_length})" if data_length else ""
                nullable_info = "NULL" if nullable == "Y" else "NOT NULL"
                default_info = f" DEFAULT {data_default}" if data_default else ""
                
                self.stdout.write(f"  {col_name:30} {data_type}{precision_info:20} {nullable_info}{default_info}")
            
            # 제약조건 확인
            cursor.execute("""
                SELECT 
                    constraint_name,
                    constraint_type,
                    search_condition
                FROM user_constraints
                WHERE table_name = 'COMPANY_FINANCIAL_STATUS'
            """)
            
            self.stdout.write('\n제약조건:')
            self.stdout.write('-'*60)
            constraints = cursor.fetchall()
            if constraints:
                for row in constraints:
                    constraint_name, constraint_type, search_condition = row
                    condition_info = f" ({search_condition})" if search_condition else ""
                    self.stdout.write(f"  {constraint_name:40} {constraint_type}{condition_info}")
            else:
                self.stdout.write("  제약조건 없음")
            
            # 외래키 확인
            cursor.execute("""
                SELECT 
                    a.constraint_name,
                    a.column_name,
                    c.table_name AS ref_table,
                    c.column_name AS ref_column
                FROM user_cons_columns a
                JOIN user_constraints b ON a.constraint_name = b.constraint_name
                JOIN user_cons_columns c ON b.r_constraint_name = c.constraint_name
                WHERE b.table_name = 'COMPANY_FINANCIAL_STATUS'
                AND b.constraint_type = 'R'
            """)
            
            self.stdout.write('\n외래키:')
            self.stdout.write('-'*60)
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                for row in foreign_keys:
                    constraint_name, column_name, ref_table, ref_column = row
                    self.stdout.write(f"  {column_name} -> {ref_table}.{ref_column}")
            else:
                self.stdout.write("  외래키 없음")
            
            # 샘플 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM COMPANY_FINANCIAL_STATUS")
            count = cursor.fetchone()[0]
            self.stdout.write(f'\n현재 데이터 개수: {count}')
            
            if count > 0:
                cursor.execute("SELECT * FROM COMPANY_FINANCIAL_STATUS WHERE ROWNUM <= 3")
                self.stdout.write('\n샘플 데이터 (최대 3개):')
                self.stdout.write('-'*60)
                columns = [desc[0] for desc in cursor.description]
                self.stdout.write("  " + " | ".join(f"{col:15}" for col in columns))
                for row in cursor.fetchall():
                    self.stdout.write("  " + " | ".join(f"{str(val):15}" for val in row))

