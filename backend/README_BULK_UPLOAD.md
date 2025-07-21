# 회사 데이터 일괄 업로드 가이드

## 개요
이 문서는 CSV 파일을 통해 회사 데이터를 일괄 업로드하는 방법을 설명합니다.

## CSV 파일 형식

### 필수 컬럼
- `company_name`: 회사명 (필수)
- `sales_diary_company_code`: 영업일지 회사코드
- `company_code_sm`: SM 회사코드
- `company_code_sap`: SAP 회사코드
- `company_type`: 회사유형
- `established_date`: 설립일 (YYYY-MM-DD 형식)
- `ceo_name`: 대표자명
- `address`: 주소
- `contact_person`: 담당자
- `contact_phone`: 담당자 연락처
- `main_phone`: 대표전화
- `distribution_type_sap`: SAP 유통유형
- `industry_name`: 업종명
- `main_product`: 주요제품
- `transaction_start_date`: 거래시작일 (YYYY-MM-DD 형식)
- `payment_terms`: 결제조건
- `customer_classification`: 고객분류 (기존/신규)
- `website`: 웹사이트
- `remarks`: 비고

## 업로드 명령어

### 기본 업로드
```bash
python manage.py import_companies <CSV파일경로>
```

### 기존 데이터 삭제 후 업로드
```bash
python manage.py import_companies <CSV파일경로> --clear
```

## 예시

### 1. 기본 업로드
```bash
python manage.py import_companies Company-2025-07-15.csv
```

### 2. 기존 데이터 삭제 후 업로드
```bash
python manage.py import_companies Company-2025-07-15.csv --clear
```

## 기능

### 중복 처리
- 회사명을 기준으로 중복을 확인합니다
- 기존 데이터가 있으면 업데이트, 없으면 새로 생성합니다

### 데이터 검증
- 날짜 필드는 YYYY-MM-DD 형식으로 자동 변환됩니다
- 빈 필드는 None으로 처리됩니다

### 트랜잭션 처리
- 모든 업로드는 트랜잭션으로 처리되어 오류 시 롤백됩니다

## API 엔드포인트

### 회사 목록 조회
```
GET /api/companies/
```

### 검색 기능
```
GET /api/companies/?search=검색어
GET /api/companies/?customer_classification=기존
GET /api/companies/?industry_name=축육
```

### 검색 파라미터
- `search`: 회사명, 대표자명, 담당자, 주소에서 검색
- `customer_classification`: 고객분류로 필터링
- `industry_name`: 업종명으로 필터링

## 데이터 확인

업로드된 데이터를 확인하려면:

```bash
python check_companies.py
```

이 스크립트는 다음 정보를 출력합니다:
- 총 회사 수
- 샘플 데이터 (처음 5개)
- 고객분류별 통계

## 주의사항

1. CSV 파일은 UTF-8 인코딩으로 저장해야 합니다
2. 날짜 필드는 YYYY-MM-DD 형식이어야 합니다
3. 대용량 파일 업로드 시 시간이 걸릴 수 있습니다
4. `--clear` 옵션 사용 시 기존 데이터가 모두 삭제됩니다 