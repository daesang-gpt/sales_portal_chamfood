#!/usr/bin/env python
"""
Raw SQL로 영업일지 데이터 확인 스크립트
"""
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

def check_report_with_raw_sql(report_id):
    """Raw SQL로 영업일지 확인"""
    print("=" * 80)
    print(f"영업일지 ID {report_id} - Raw SQL 조회 결과")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # 모든 컬럼 조회
        cursor.execute("""
            SELECT 
                ID,
                AUTHOR_ID,
                AUTHOR_NAME,
                AUTHOR_DEPARTMENT,
                VISIT_DATE,
                COMPANY_CODE,
                COMPANY_NAME,
                COMPANY_CITY_DISTRICT,
                SALES_STAGE,
                TYPE,
                PRODUCTS,
                CONTENT,
                TAGS,
                CREATED_AT
            FROM REPORTS 
            WHERE ID = %s
        """, [report_id])
        
        result = cursor.fetchone()
        
        if result:
            columns = [
                'ID', 'AUTHOR_ID', 'AUTHOR_NAME', 'AUTHOR_DEPARTMENT',
                'VISIT_DATE', 'COMPANY_CODE', 'COMPANY_NAME', 'COMPANY_CITY_DISTRICT',
                'SALES_STAGE', 'TYPE', 'PRODUCTS', 'CONTENT', 'TAGS', 'CREATED_AT'
            ]
            
            print(f"영업일지 ID {report_id} 상세 정보:")
            print("-" * 80)
            
            for i, col in enumerate(columns):
                value = result[i]
                value_type = type(value).__name__
                
                # 내용이 긴 경우 축약
                if isinstance(value, str) and len(value) > 100:
                    display_value = f"'{value[:100]}...' (길이: {len(value)})"
                else:
                    display_value = repr(value)
                
                print(f"{col:<20}: {display_value} ({value_type})")
            
            # company_code 특별 분석
            company_code = result[5]  # COMPANY_CODE 컬럼
            print("\n" + "=" * 40 + " COMPANY_CODE 분석 " + "=" * 40)
            print(f"COMPANY_CODE 원본값: {repr(company_code)}")
            print(f"타입: {type(company_code).__name__}")
            print(f"is None: {company_code is None}")
            print(f"== '': {company_code == ''}")
            print(f"== 'None': {company_code == 'None'}")
            
            if company_code:
                print(f"문자열 길이: {len(str(company_code))}")
                print(f"문자열 표현: '{company_code}'")
                
                # 해당 company_code로 회사 검색
                cursor.execute("SELECT COMPANY_CODE, COMPANY_NAME FROM COMPANIES WHERE COMPANY_CODE = %s", [company_code])
                company_result = cursor.fetchone()
                if company_result:
                    print(f"연결된 회사 발견: {company_result[0]} - {company_result[1]}")
                else:
                    print("해당 company_code에 매칭되는 회사 없음")
            else:
                print("COMPANY_CODE가 비어있음 (None 또는 빈 문자열)")
                
                # company_name으로 회사 검색
                company_name = result[6]  # COMPANY_NAME 컬럼
                if company_name:
                    print(f"\nCOMPANY_NAME으로 회사 검색: '{company_name}'")
                    cursor.execute("SELECT COMPANY_CODE, COMPANY_NAME FROM COMPANIES WHERE COMPANY_NAME = %s", [company_name])
                    companies = cursor.fetchall()
                    if companies:
                        print(f"동일한 이름의 회사들:")
                        for comp in companies:
                            print(f"  - {comp[0]}: {comp[1]}")
                    else:
                        print("동일한 이름의 회사 없음")
                        
        else:
            print(f"영업일지 ID {report_id}를 찾을 수 없습니다.")

def check_company_in_db(company_code):
    """회사 존재 여부 Raw SQL 확인"""
    print("=" * 80)
    print(f"회사코드 {company_code} DB 확인")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COMPANY_CODE, COMPANY_NAME, CUSTOMER_CLASSIFICATION, 
                   COMPANY_TYPE, CEO_NAME, CITY_DISTRICT
            FROM COMPANIES 
            WHERE COMPANY_CODE = %s
        """, [company_code])
        
        result = cursor.fetchone()
        if result:
            print(f"✅ 회사 발견!")
            print(f"회사코드: {result[0]}")
            print(f"회사명: {result[1]}")
            print(f"고객분류: {result[2]}")
            print(f"회사유형: {result[3]}")
            print(f"대표자: {result[4]}")
            print(f"시/구: {result[5]}")
        else:
            print(f"❌ 회사코드 {company_code}를 찾을 수 없습니다.")

def main():
    # 먼저 올리브푸드 회사 존재 확인
    check_company_in_db('C0000546')
    
    print("\n")
    
    # 영업일지 7462 확인 (올리브푸드 영업일지)
    check_report_with_raw_sql(7462)
    
    # 비교용으로 기존 영업일지도 확인 (쿠즈락)
    print("\n\n" + "=" * 40 + " 비교: 쿠즈락 영업일지 " + "=" * 40)
    check_report_with_raw_sql(7113)
    
    print("\n" + "=" * 80)
    print("Raw SQL 조회 완료")
    print("=" * 80)

if __name__ == '__main__':
    main()
