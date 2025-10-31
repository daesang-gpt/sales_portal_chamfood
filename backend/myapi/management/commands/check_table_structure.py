from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'COMPANY_FINANCIAL_STATUS 테이블 구조를 상세히 확인합니다'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # 테이블 컬럼 상세 정보
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
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write('COMPANY_FINANCIAL_STATUS 테이블 구조')
            self.stdout.write('='*80)
            
            for row in cursor.fetchall():
                col_name, data_type, data_length, data_precision, data_scale, nullable, data_default = row
                self.stdout.write(f'\n컬럼명: {col_name}')
                self.stdout.write(f'  데이터 타입: {data_type}')
                if data_precision:
                    self.stdout.write(f'  Precision: {data_precision}')
                if data_scale:
                    self.stdout.write(f'  Scale: {data_scale}')
                if data_length:
                    self.stdout.write(f'  길이: {data_length}')
                self.stdout.write(f'  NULL 허용: {nullable}')
                if data_default:
                    self.stdout.write(f'  기본값: {data_default}')
            
            # 외래키 정보
            cursor.execute("""
                SELECT 
                    a.constraint_name,
                    a.column_name,
                    c_pk.table_name AS references_table,
                    b.column_name AS references_column
                FROM user_cons_columns a
                JOIN user_constraints c ON a.constraint_name = c.constraint_name
                LEFT JOIN user_cons_columns b ON c.r_constraint_name = b.constraint_name
                LEFT JOIN user_constraints c_pk ON b.constraint_name = c_pk.constraint_name
                WHERE c.constraint_type = 'R'
                AND a.table_name = 'COMPANY_FINANCIAL_STATUS'
            """)
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write('외래키 정보')
            self.stdout.write('='*80)
            
            fk_rows = cursor.fetchall()
            if fk_rows:
                for row in fk_rows:
                    constraint_name, column_name, ref_table, ref_column = row
                    self.stdout.write(f'\n제약조건: {constraint_name}')
                    self.stdout.write(f'  컬럼: {column_name}')
                    self.stdout.write(f'  참조 테이블: {ref_table}')
                    self.stdout.write(f'  참조 컬럼: {ref_column}')
            else:
                self.stdout.write('\n외래키 없음')
            
            self.stdout.write('\n' + '='*80)

