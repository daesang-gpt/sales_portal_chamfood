from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'COMPANIES 테이블 구조를 확인합니다'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Primary Key 확인
            cursor.execute("""
                SELECT 
                    a.column_name,
                    a.data_type
                FROM user_tab_columns a
                WHERE a.table_name = 'COMPANIES'
                AND a.column_name IN ('ID', 'COMPANY_CODE')
                ORDER BY a.column_id
            """)
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write('COMPANIES 테이블 주요 컬럼')
            self.stdout.write('='*80)
            
            for row in cursor.fetchall():
                col_name, data_type = row
                self.stdout.write(f'{col_name}: {data_type}')
            
            # Primary Key 제약조건 확인
            cursor.execute("""
                SELECT 
                    a.column_name,
                    c.constraint_name
                FROM user_cons_columns a
                JOIN user_constraints c ON a.constraint_name = c.constraint_name
                WHERE c.constraint_type = 'P'
                AND a.table_name = 'COMPANIES'
            """)
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write('Primary Key')
            self.stdout.write('='*80)
            
            for row in cursor.fetchall():
                col_name, constraint_name = row
                self.stdout.write(f'PK 컬럼: {col_name} (제약조건: {constraint_name})')
            
            self.stdout.write('\n' + '='*80)

