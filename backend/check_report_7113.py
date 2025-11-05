#!/usr/bin/env python
"""
영업일지 ID 7113의 회사코드 정보를 확인하는 스크립트
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.models import Report

def check_report_7113():
    print('=== 영업일지 ID 7113 상세 정보 ===')
    
    try:
        report = Report.objects.get(id=7113)
        print(f'영업일지 ID: {report.id}')
        print(f'회사명 (company_name): {repr(report.company_name)}')
        print(f'회사코드 (company_code): {repr(report.company_code)}')
        print(f'작성자: {report.author_name}')
        print(f'작성일: {report.created_at}')
        print(f'방문일: {report.visit_date}')
        print(f'영업단계: {report.sales_stage}')
        
        # company_code 필드의 타입과 값 상세 확인
        print(f'\n=== company_code 상세 분석 ===')
        print(f'company_code 값: {report.company_code}')
        print(f'company_code 타입: {type(report.company_code)}')
        print(f'company_code is None: {report.company_code is None}')
        print(f'company_code == "": {report.company_code == ""}')
        
        if report.company_code:
            print(f'company_code 문자열 길이: {len(str(report.company_code))}')
            print(f'company_code 문자열 표현: "{report.company_code}"')
        else:
            print('company_code는 비어있습니다 (None 또는 빈 문자열)')
            
        # FK 관계 확인
        print(f'\n=== FK 관계 확인 ===')
        if hasattr(report, 'company_code') and report.company_code:
            try:
                from myapi.models import Company
                company = Company.objects.get(company_code=report.company_code)
                print(f'연결된 회사: {company}')
            except Company.DoesNotExist:
                print('company_code에 해당하는 회사가 존재하지 않음')
        else:
            print('FK 연결 없음 (company_code가 비어있음)')

    except Report.DoesNotExist:
        print('영업일지 ID 7113을 찾을 수 없습니다.')
    except Exception as e:
        print(f'오류 발생: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_report_7113()
