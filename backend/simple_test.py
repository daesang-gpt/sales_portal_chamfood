import requests
import json

def test_keyword_extraction():
    # 로그인
    login_data = {
        "id": "admin",
        "password": "admin1234"
    }
    
    login_response = requests.post(
        "http://localhost:8000/api/login/",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        access_token = login_result.get('access_token')
        
        print("로그인 성공!")
        
        # 테스트 텍스트
        test_text = "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다."
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        keywords_data = {
            "text": test_text
        }
        
        print(f"입력 텍스트: {test_text}")
        
        keywords_response = requests.post(
            "http://localhost:8000/api/extract-keywords/",
            json=keywords_data,
            headers=headers
        )
        
        if keywords_response.status_code == 200:
            result = keywords_response.json()
            print(f"추출된 키워드: {result['keywords']}")
            
            # 특정 키워드 확인
            if "유통경로" in result['keywords']:
                print("✅ '유통경로' 키워드가 성공적으로 추출되었습니다!")
            else:
                print("❌ '유통경로' 키워드가 추출되지 않았습니다.")
        else:
            print(f"키워드 추출 실패: {keywords_response.status_code}")
            print(f"응답: {keywords_response.text}")
    else:
        print(f"로그인 실패: {login_response.status_code}")

if __name__ == "__main__":
    test_keyword_extraction() 