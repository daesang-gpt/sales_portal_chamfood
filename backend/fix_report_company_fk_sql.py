"""
영업일지의 company_code FK 연결 수정 스크립트 (SQL 직접 사용)
Oracle에서 FK를 문자열로 직접 업데이트합니다.
"""
import os
import django

# Django 설정 로드
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django.setup()

from django.db import connection

def fix_report_company_fk_sql():
    print("=" * 80)
    print("영업일지의 company_code FK 연결 수정 시작 (SQL 직접 사용)")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # 1단계: 회사명 + 소재지로 정확히 매칭
        print("\n[1단계] 회사명 + 소재지로 매칭")
        sql1 = """
            UPDATE "REPORTS" r
            SET r."COMPANY_CODE" = (
                SELECT c."COMPANY_CODE" 
                FROM "COMPANIES" c 
                WHERE c."COMPANY_NAME" = r."COMPANY_NAME" 
                  AND NVL(c."CITY_DISTRICT", '') = NVL(r."COMPANY_CITY_DISTRICT", '')
            )
            WHERE r."COMPANY_CODE" IS NULL 
              AND r."COMPANY_NAME" IS NOT NULL
              AND EXISTS (
                  SELECT 1 
                  FROM "COMPANIES" c 
                  WHERE c."COMPANY_NAME" = r."COMPANY_NAME" 
                    AND NVL(c."CITY_DISTRICT", '') = NVL(r."COMPANY_CITY_DISTRICT", '')
                  GROUP BY c."COMPANY_NAME", NVL(c."CITY_DISTRICT", '')
                  HAVING COUNT(*) = 1
              )
        """
        cursor.execute(sql1)
        count1 = cursor.rowcount
        print(f"  - 수정된 영업일지 수: {count1}개")
        
        # 2단계: 회사명만으로 매칭 (소재지가 없거나 위에서 못 찾은 경우, 단일 매칭만)
        print("\n[2단계] 회사명만으로 매칭 (단일 매칭만)")
        sql2 = """
            UPDATE "REPORTS" r
            SET r."COMPANY_CODE" = (
                SELECT c."COMPANY_CODE" 
                FROM "COMPANIES" c 
                WHERE c."COMPANY_NAME" = r."COMPANY_NAME"
            )
            WHERE r."COMPANY_CODE" IS NULL 
              AND r."COMPANY_NAME" IS NOT NULL
              AND EXISTS (
                  SELECT 1 
                  FROM "COMPANIES" c 
                  WHERE c."COMPANY_NAME" = r."COMPANY_NAME"
                  GROUP BY c."COMPANY_NAME"
                  HAVING COUNT(*) = 1
              )
        """
        cursor.execute(sql2)
        count2 = cursor.rowcount
        print(f"  - 수정된 영업일지 수: {count2}개")
        
        # 최종 상태 확인
        print("\n[최종 상태 확인]")
        cursor.execute('SELECT COUNT(*) FROM "REPORTS" WHERE "COMPANY_CODE" IS NULL')
        remaining = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM "REPORTS" WHERE "COMPANY_CODE" IS NOT NULL')
        fixed = cursor.fetchone()[0]
        print(f"  - company_code FK가 있는 영업일지: {fixed}개")
        print(f"  - company_code FK가 없는 영업일지: {remaining}개")
        print(f"  - 총 수정된 영업일지: {count1 + count2}개")
    
    print("\n" + "=" * 80)
    print("수정 완료!")
    print("=" * 80)

if __name__ == '__main__':
    fix_report_company_fk_sql()

