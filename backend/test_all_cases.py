import requests
import json
import time

def test_all_cases():
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
        
        # 테스트 케이스들
        test_cases = [
            {
                "text": "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다.",
                "expected": ["유통경로", "단축", "경쟁사", "가격 메리트"]
            },
            {
                "text": "제품 품질에 대한 우려가 있었으며, 배송 일정 조정이 필요하다고 하셨습니다.",
                "expected": ["품질", "우려", "일정", "조정"]
            },
            {
                "text": "신규 계약 조건 협상에서 할인율과 지불 조건에 대해 논의했습니다.",
                "expected": ["신규", "계약", "협상", "할인율", "지불 조건"]
            },
            {
                "text": "고객사에서 새로운 기능 개발 요청이 있었고, 기술 지원팀과 협의가 필요합니다.",
                "expected": ["개발 요청", "기술 지원팀", "협의"]
            },
            {
                "text": "브라질산 닭정육과 호주산 목전지 매입 협의를 진행했습니다.",
                "expected": ["브라질산", "닭정육", "호주산", "목전지", "매입", "협의"]
            },
            {
                "text": "스미스필드 삼겹과 그로스퍼트너 목전지 납품 일정을 조율했습니다.",
                "expected": ["스미스필드", "삼겹", "그로스퍼트너", "목전지", "납품", "일정"]
            }
        ]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n=== 테스트 케이스 {i} ===")
            print(f"입력 텍스트: {case['text']}")
            print(f"기대 키워드: {case['expected']}")
            
            start_time = time.time()
            
            keywords_data = {
                "text": case['text']
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
                extracted_keywords = result['keywords']
                print(f"추출된 키워드: {extracted_keywords}")
                print(f"처리 시간: {processing_time:.2f}초")
                
                # 정확도 계산
                correct_count = 0
                for expected in case['expected']:
                    if expected in extracted_keywords:
                        correct_count += 1
                        print(f"✅ '{expected}' 추출됨")
                    else:
                        print(f"❌ '{expected}' 누락됨")
                
                accuracy = correct_count / len(case['expected']) * 100
                print(f"정확도: {accuracy:.1f}% ({correct_count}/{len(case['expected'])})")
                
            else:
                print(f"키워드 추출 실패: {keywords_response.status_code}")
                print(f"응답: {keywords_response.text}")
            
            # API 호출 간격 조절
            time.sleep(1)
            
    else:
        print(f"로그인 실패: {login_response.status_code}")

if __name__ == "__main__":
    test_all_cases() 