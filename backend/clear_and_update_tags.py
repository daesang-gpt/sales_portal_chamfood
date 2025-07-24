import os
import sys
import django
import requests
import json
import time
from django.db import models

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import Report

def get_access_token():
    """관리자로 로그인하여 액세스 토큰을 받습니다."""
    login_data = {
        "id": "admin",
        "password": "admin1234"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('access_token')
        else:
            print(f"로그인 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"로그인 중 오류: {e}")
        return None

def extract_keywords_from_text(text, access_token):
    """새로운 키워드 추출 API를 호출합니다."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    keywords_data = {
        "text": text
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/extract-keywords/",
            json=keywords_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('keywords', [])
        else:
            print(f"키워드 추출 실패: {response.status_code}")
            return []
    except Exception as e:
        print(f"키워드 추출 중 오류: {e}")
        return []

def clear_all_tags():
    """모든 영업일지의 태그를 삭제합니다."""
    try:
        # 모든 영업일지의 태그를 빈 문자열로 설정
        updated_count = Report.objects.all().update(tags='')
        print(f"총 {updated_count}개의 영업일지 태그를 삭제했습니다.")
        return updated_count
    except Exception as e:
        print(f"태그 삭제 중 오류: {e}")
        return 0

def update_report_tags():
    """영업일지의 content를 기반으로 새로운 태그를 생성합니다."""
    access_token = get_access_token()
    if not access_token:
        print("액세스 토큰을 받을 수 없습니다.")
        return
    
    print("새로운 KR-SBERT + KeyBERT API로 태그를 업데이트합니다...")
    
    # content가 있는 모든 영업일지 조회
    reports_to_update = Report.objects.exclude(
        content__isnull=True
    ).exclude(content__exact='')
    
    total_count = reports_to_update.count()
    print(f"업데이트할 영업일지 수: {total_count}")
    
    if total_count == 0:
        print("업데이트할 영업일지가 없습니다.")
        return
    
    success_count = 0
    error_count = 0
    
    for i, report in enumerate(reports_to_update, 1):
        try:
            print(f"처리 중... ({i}/{total_count}) - ID: {report.id}")
            
            # 키워드 추출
            keywords = extract_keywords_from_text(report.content, access_token)
            
            if keywords:
                # 키워드를 콤마로 구분된 문자열로 변환
                tags_string = ', '.join(keywords)
                report.tags = tags_string
                report.save()
                success_count += 1
                print(f"  ✅ 성공: {tags_string}")
            else:
                print(f"  ⚠️ 키워드 추출 실패")
                error_count += 1
            
            # API 호출 간격 조절 (서버 부하 방지)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            error_count += 1
    
    print(f"\n=== 업데이트 완료 ===")
    print(f"총 처리: {total_count}개")
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")

def show_sample_results():
    """샘플 결과를 보여줍니다."""
    print("\n=== 샘플 결과 ===")
    sample_reports = Report.objects.exclude(tags__isnull=True).exclude(tags__exact='')[:5]
    
    for report in sample_reports:
        print(f"ID: {report.id}")
        print(f"Content: {report.content[:100]}...")
        print(f"Tags: {report.tags}")
        print("-" * 50)

if __name__ == "__main__":
    print("=== 영업일지 태그 교체 작업 시작 ===")
    
    # 1단계: 기존 태그 삭제
    print("\n1단계: 기존 태그 삭제 중...")
    clear_all_tags()
    
    # 2단계: 새로운 API로 태그 업데이트
    print("\n2단계: 새로운 API로 태그 업데이트 중...")
    update_report_tags()
    
    # 3단계: 샘플 결과 확인
    show_sample_results()
    
    print("\n=== 작업 완료 ===") 