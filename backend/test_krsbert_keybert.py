import requests
import json
import time

def test_krsbert_keybert_api():
    # 로그인하여 토큰 받기
    login_data = {
        "id": "admin",
        "password": "admin1234"
    }
    
    try:
        # 로그인
        login_response = requests.post(
            "http://localhost:8000/api/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access_token')
            
            print("로그인 성공!")
            
            # 다양한 테스트 케이스
            test_cases = [
                "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다.",
                "제품 품질에 대한 우려가 있었으며, 배송 일정 조정이 필요하다고 하셨습니다.",
                "신규 계약 조건 협상에서 할인율과 지불 조건에 대해 논의했습니다.",
                "고객사에서 새로운 기능 개발 요청이 있었고, 기술 지원팀과 협의가 필요합니다.",
                "브라질산 닭정육과 호주산 목전지 매입 협의를 진행했습니다.",
                "스미스필드 삼겹과 그로스퍼트너 목전지 납품 일정을 조율했습니다."
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            for i, test_text in enumerate(test_cases, 1):
                print(f"\n=== 테스트 케이스 {i} ===")
                print(f"입력 텍스트: {test_text}")
                
                start_time = time.time()
                
                keywords_data = {
                    "text": test_text
                }
                
                keywords_response = requests.post(
                    "http://localhost:8000/api/extract-keywords/",
                    json=keywords_data,
                    headers=headers
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                if keywords_response.status_code == 200:
                    result = keywords_response.json()
                    print(f"추출된 키워드: {result['keywords']}")
                    print(f"처리 시간: {processing_time:.2f}초")
                    
                    # 특정 키워드 확인
                    if i == 1:  # 첫 번째 테스트 케이스
                        if "유통경로" in result['keywords']:
                            print("✅ '유통경로' 키워드가 성공적으로 추출되었습니다!")
                        else:
                            print("❌ '유통경로' 키워드가 추출되지 않았습니다.")
                            
                else:
                    print(f"키워드 추출 실패: {keywords_response.status_code}")
                    print(f"응답: {keywords_response.text}")
                
                # API 호출 간격 조절
                time.sleep(1)
                
        else:
            print(f"로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("서버에 연결할 수 없습니다. Django 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    test_krsbert_keybert_api() 