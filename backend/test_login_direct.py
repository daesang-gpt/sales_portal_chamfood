import os
import django
import json

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.test import Client
from myapi.models import User

def test_login_api():
    client = Client()
    
    # 관리자 계정 확인
    admin = User.objects.filter(username='admin').first()
    if not admin:
        print("❌ 관리자 계정이 존재하지 않습니다!")
        return
    
    print(f"✅ 관리자 계정 확인: {admin.username} ({admin.name})")
    
    # 로그인 테스트
    login_data = {
        'id': 'admin',
        'password': 'admin1234'
    }
    
    print(f"\n=== 로그인 API 테스트 ===")
    print(f"데이터: {login_data}")
    
    try:
        response = client.post('/api/login/', data=json.dumps(login_data), content_type='application/json')
        
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 로그인 성공!")
            print(f"응답: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 로그인 실패!")
            print(f"응답: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == '__main__':
    test_login_api() 