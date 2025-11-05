from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'SALES_DATA 테이블의 컬럼명을 확인합니다'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tables 
                WHERE table_name = 'SALES_DATA'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                self.stdout.write(self.style.ERROR('테이블 SALES_DATA가 존재하지 않습니다.'))
                return
            
            self.stdout.write(self.style.SUCCESS('테이블 SALES_DATA 존재 확인됨'))
            self.stdout.write('='*60)
            
            # 중량 관련 컬럼명 확인
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    nullable
                FROM user_tab_columns
                WHERE table_name = 'SALES_DATA'
                AND (
                    UPPER(column_name) LIKE '%WEIGHT%' 
                    OR UPPER(column_name) LIKE '%중량%'
                    OR column_name LIKE '%중량%'
                )
                ORDER BY column_id
            """)
            
            self.stdout.write('\n중량 관련 컬럼:')
            self.stdout.write('-'*60)
            for row in cursor.fetchall():
                col_name, data_type, nullable = row
                self.stdout.write(f'컬럼명: {col_name} (타입: {data_type}, NULL: {nullable})')
            
            # 모든 컬럼명 확인
            cursor.execute("""
                SELECT 
                    column_name
                FROM user_tab_columns
                WHERE table_name = 'SALES_DATA'
                ORDER BY column_id
            """)
            
            self.stdout.write('\n\n모든 컬럼명:')
            self.stdout.write('-'*60)
            for row in cursor.fetchall():
                self.stdout.write(f'  {row[0]}')

