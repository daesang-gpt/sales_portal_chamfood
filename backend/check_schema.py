"""
DB 스키마 확인 - REPORTS 테이블의 COMPANY_CODE 컬럼 타입 확인
"""
import os
import django

# Django 설정 로드
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django.setup()

from django.db import connection

def check_schema():
    with connection.cursor() as cursor:
        # REPORTS 테이블의 COMPANY_CODE 컬럼 타입 확인
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH 
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'REPORTS' 
            AND COLUMN_NAME = 'COMPANY_CODE'
        """)
        result = cursor.fetchone()
        if result:
            print(f"REPORTS.COMPANY_CODE 컬럼 타입: {result[1]} (길이: {result[2]})")
        else:
            print("REPORTS.COMPANY_CODE 컬럼을 찾을 수 없습니다.")
        
        # COMPANIES 테이블의 COMPANY_CODE 컬럼 타입 확인
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH 
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'COMPANIES' 
            AND COLUMN_NAME = 'COMPANY_CODE'
        """)
        result = cursor.fetchone()
        if result:
            print(f"COMPANIES.COMPANY_CODE 컬럼 타입: {result[1]} (길이: {result[2]})")
        else:
            print("COMPANIES.COMPANY_CODE 컬럼을 찾을 수 없습니다.")
        
        # 샘플 데이터 확인
        cursor.execute('SELECT "COMPANY_CODE" FROM "REPORTS" WHERE "COMPANY_CODE" IS NOT NULL FETCH FIRST 1 ROWS ONLY')
        sample = cursor.fetchone()
        if sample:
            print(f"REPORTS 테이블의 COMPANY_CODE 샘플 값: {sample[0]} (타입: {type(sample[0])})")
        
        cursor.execute('SELECT "COMPANY_CODE" FROM "COMPANIES" FETCH FIRST 1 ROWS ONLY')
        sample = cursor.fetchone()
        if sample:
            print(f"COMPANIES 테이블의 COMPANY_CODE 샘플 값: {sample[0]} (타입: {type(sample[0])})")

if __name__ == '__main__':
    check_schema()

