import os
import django
import requests
import json
import time

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import Report, User
from django.db import models

def get_access_token():
    """관리자 계정으로 로그인하여 액세스 토큰을 받습니다."""
    login_data = {
        "id": "admin",
        "password": "admin1234"
    }
    
    try:
        login_response = requests.post(
            "http://localhost:8000/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            return login_result.get('access_token')
        else:
            print(f"로그인 실패: {login_response.status_code}")
            return None
            
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return None

def extract_keywords_from_text(text, access_token):
    """키워드 추출 API를 사용하여 텍스트에서 키워드를 추출합니다."""
    if not text or not text.strip():
        return []
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    keywords_data = {
        "text": text
    }
    
    try:
        keywords_response = requests.post(
            "http://localhost:8000/api/extract-keywords/",
            json=keywords_data,
            headers=headers
        )
        
        if keywords_response.status_code == 200:
            result = keywords_response.json()
            return result.get('keywords', [])
        else:
            print(f"키워드 추출 실패: {keywords_response.status_code}")
            return []
            
    except Exception as e:
        print(f"키워드 추출 중 오류 발생: {e}")
        return []

def update_report_tags():
    """기존 영업일지 데이터의 content를 이용해서 tags를 업데이트합니다."""
    
    # 액세스 토큰 받기
    access_token = get_access_token()
    if not access_token:
        print("액세스 토큰을 받을 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return
    
    print("액세스 토큰을 성공적으로 받았습니다.")
    
    # content가 있는 모든 영업일지 조회 (기존 tags 무시하고 모두 업데이트)
    reports_to_update = Report.objects.exclude(
        content__isnull=True
    ).exclude(content__exact='')
    
    total_reports = reports_to_update.count()
    print(f"업데이트할 영업일지 수: {total_reports}")
    
    if total_reports == 0:
        print("업데이트할 영업일지가 없습니다.")
        return
    
    updated_count = 0
    error_count = 0
    
    for i, report in enumerate(reports_to_update, 1):
        try:
            print(f"\n처리 중... ({i}/{total_reports})")
            print(f"회사: {report.company}, 방문일: {report.visitDate}")
            print(f"내용 미리보기: {report.content[:100]}...")
            
            # 키워드 추출
            keywords = extract_keywords_from_text(report.content, access_token)
            
            if keywords:
                # 키워드를 콤마로 구분된 문자열로 변환
                tags_string = ', '.join(keywords)
                report.tags = tags_string
                report.save()
                
                print(f"✅ 태그 업데이트 완료: {tags_string}")
                updated_count += 1
            else:
                print("⚠️ 키워드가 추출되지 않았습니다.")
                error_count += 1
            
            # API 호출 간격 조절 (서버 부하 방지)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            error_count += 1
            continue
    
    print(f"\n=== 업데이트 완료 ===")
    print(f"총 처리: {total_reports}개")
    print(f"성공: {updated_count}개")
    print(f"실패: {error_count}개")

def show_sample_results():
    """업데이트된 결과 샘플을 보여줍니다."""
    print("\n=== 업데이트된 영업일지 샘플 ===")
    
    # 최근에 업데이트된 영업일지 5개 조회
    recent_reports = Report.objects.filter(
        tags__isnull=False
    ).exclude(tags__exact='').order_by('-createdAt')[:5]
    
    for report in recent_reports:
        print(f"\n회사: {report.company}")
        print(f"방문일: {report.visitDate}")
        print(f"내용: {report.content[:100]}...")
        print(f"태그: {report.tags}")
        print("-" * 50)

if __name__ == "__main__":
    print("영업일지 태그 업데이트를 시작합니다...")
    
    # Django 서버가 실행 중인지 확인
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("Django 서버가 실행 중입니다.")
    except:
        print("❌ Django 서버가 실행되지 않았습니다.")
        print("python manage.py runserver 명령으로 서버를 먼저 실행해주세요.")
        exit(1)
    
    # 태그 업데이트 실행
    update_report_tags()
    
    # 결과 샘플 보여주기
    show_sample_results() 