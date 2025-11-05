from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'SALES_DATA 테이블의 중량_KG 컬럼을 WEIGHT_KG로 변경합니다'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # 기존 컬럼이 존재하는지 확인
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_tab_columns 
                    WHERE table_name = 'SALES_DATA' 
                    AND column_name = '중량_KG'
                """)
                if cursor.fetchone()[0] == 0:
                    self.stdout.write(self.style.WARNING('중량_KG 컬럼이 존재하지 않습니다.'))
                    return
                
                # 새 컬럼명이 이미 존재하는지 확인
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM user_tab_columns 
                    WHERE table_name = 'SALES_DATA' 
                    AND column_name = 'WEIGHT_KG'
                """)
                if cursor.fetchone()[0] > 0:
                    self.stdout.write(self.style.WARNING('WEIGHT_KG 컬럼이 이미 존재합니다.'))
                    return
                
                # 컬럼명 변경
                cursor.execute('ALTER TABLE "SALES_DATA" RENAME COLUMN "중량_KG" TO "WEIGHT_KG"')
                self.stdout.write(self.style.SUCCESS('중량_KG 컬럼을 WEIGHT_KG로 성공적으로 변경했습니다.'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'오류 발생: {str(e)}'))
                raise

