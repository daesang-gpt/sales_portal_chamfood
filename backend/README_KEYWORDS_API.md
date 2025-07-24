# 키워드 추출 API 문서

## 개요
영업일지의 미팅 내용에서 주요 키워드(단어)를 빠르게 추출하는 API입니다.

## 기술 스택
- **라이브러리**: YAKE (Yet Another Keyword Extractor)
- **라이선스**: MIT (상업적 사용 가능)
- **언어 지원**: 한국어 최적화
- **응답 속도**: 빠른 처리 (실시간)

## API 엔드포인트

### 키워드 추출 API
- **URL**: `/api/extract-keywords/`
- **메서드**: `POST`
- **인증**: JWT 토큰 필요

### 요청 형식
```json
{
    "text": "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다."
}
```

### 응답 형식
```json
{
    "keywords": ["유통경로", "고객", "요구", "경쟁사", "응답", "단축", "메리트"]
}
```

## 사용 예시

### Python 예시
```python
import requests

# 로그인하여 토큰 받기
login_response = requests.post(
    "http://localhost:8000/api/login/",
    json={"id": "admin", "password": "admin123"}
)
access_token = login_response.json()['access_token']

# 키워드 추출
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

keywords_response = requests.post(
    "http://localhost:8000/api/extract-keywords/",
    json={"text": "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다."},
    headers=headers
)

keywords = keywords_response.json()['keywords']
print(keywords)
```

### cURL 예시
```bash
# 로그인
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"id": "admin", "password": "admin123"}'

# 키워드 추출 (토큰 사용)
curl -X POST http://localhost:8000/api/extract-keywords/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"text": "고객은 유통경로 단축을 요구했고, 경쟁사보다 가격 메리트가 없다고 응답했습니다."}'
```

## 특징

### 1. 한국어 최적화
- 한국어 형태소 특성을 고려한 키워드 추출
- 조사, 어미 자동 제거
- 2글자 이상의 의미있는 키워드만 추출
- 복합어 처리 (예: "유통경로", "가격 메리트")

### 2. 빠른 처리 속도
- YAKE 라이브러리의 효율적인 알고리즘 사용
- 실시간 키워드 추출 가능

### 3. 정확한 키워드 추출
- 문맥을 고려한 키워드 중요도 계산
- 중복 키워드 자동 제거
- 최대 10개 키워드 반환

## 테스트

테스트 스크립트를 실행하여 API를 테스트할 수 있습니다:

```bash
cd backend
python test_keywords_api.py
```

## 오류 처리

### 400 Bad Request
- 텍스트가 제공되지 않은 경우
```json
{
    "error": "텍스트가 필요합니다."
}
```

### 401 Unauthorized
- 유효하지 않은 토큰인 경우

### 500 Internal Server Error
- 키워드 추출 중 오류가 발생한 경우
```json
{
    "error": "키워드 추출 중 오류가 발생했습니다.",
    "detail": "오류 상세 내용"
}
```

## 라이선스
YAKE 라이브러리는 MIT 라이선스로 배포되며, 상업적 사용이 가능합니다. 