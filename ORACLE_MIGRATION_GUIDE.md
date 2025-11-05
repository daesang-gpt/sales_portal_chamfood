# 오라클 DB 마이그레이션 가이드

## 주요 변경 사항

### 1. SalesData 모델 - 한글 필드명을 영문 db_column으로 변경

**문제점**: 오라클 DB는 한글 컬럼명과 특수문자를 지원하지만, Django와의 호환성 및 쿼리 성능 문제가 발생할 수 있습니다.

**해결책**: Python 코드에서는 한글 필드명을 그대로 사용하되, DB 컬럼명은 영문으로 변경했습니다.

**변경된 필드 매핑**:
- `매출일자` → `sale_date`
- `코드` → `code`
- `거래처명` → `customer_name`
- `매출부서` → `sales_dept`
- `매출담당자` → `sales_person`
- `유통형태` → `distribution_type`
- `상품코드` → `product_code`
- `상품명` → `product_name`
- `브랜드` → `brand`
- `축종` → `livestock_type`
- `부위` → `cut_type`
- `원산지` → `origin`
- `축종_부위` → `livestock_cut`
- `원산지_축종` → `origin_livestock`
- `등급` → `grade`
- `Box` → `box`
- `중량_Kg` → `weight_kg`
- `매출단가` → `sale_unit_price`
- `매출금액` → `sale_amount`
- `매출이익` → `sale_profit`
- `이익율` → `profit_rate`
- `매입처` → `purchase_source`
- `매입일자` → `purchase_date`
- `재고보유일` → `inventory_days`
- `수입로컬` → `import_local`
- `이관재고여부` → `transfer_inventory_yn`
- `담당자` → `manager`
- `매입단가` → `purchase_unit_price`
- `매입금액` → `purchase_amount`
- `지점명` → `branch_name`
- `매출비고` → `sale_note`
- `매입비고` → `purchase_note`
- `이력번호` → `history_no`
- `BL번호` → `bl_number`

**중요**: Python 코드에서는 여전히 한글 필드명을 사용할 수 있습니다. 예: `sales_data.매출일자`, `sales_data.거래처명`

### 2. CompanyFinancialStatus 모델 - FK 수정

**문제점**: `company_id`로 지정되어 있지만 실제 PK는 `company_code`입니다.

**해결책**: `to_field='company_code'` 및 `db_column='company_code'`로 변경했습니다.

### 3. Report 모델 - 중복 FK 제거 및 필드명 개선

**변경 사항**:
- `company_obj` FK 제거 (중복 제거)
- `company_code` FK만 사용 (문자열 PK 연결)
- `visitDate` → `visit_date` (db_column)
- `createdAt` → `created_at` (db_column)

**주의**: Report 모델에서 `company_obj`를 제거했으므로, serializer와 views에서도 수정이 필요할 수 있습니다.

### 4. SalesData 모델 - company_obj FK 컬럼명 수정

**변경 사항**: `company_obj` FK의 `db_column`을 `company_code_id`로 변경하여 다른 필드와의 충돌 방지

## 마이그레이션 절차

### 1단계: 기존 데이터 백업 확인
- 기존 데이터는 이미 백업하셨다고 하셨으므로, 이 단계는 건너뛰셔도 됩니다.

### 2단계: 마이그레이션 파일 생성
```bash
cd backend
python manage.py makemigrations
```

### 3단계: 마이그레이션 파일 확인
생성된 마이그레이션 파일을 확인하여 다음 사항들이 포함되어 있는지 확인:
- SalesData 모델의 컬럼명 변경 (ALTER TABLE ... RENAME COLUMN)
- CompanyFinancialStatus의 FK 수정
- Report 모델의 컬럼명 변경 및 company_obj 제거

### 4단계: 데이터 마이그레이션 (필요시)
기존 데이터가 있다면, 마이그레이션 파일에 데이터 마이그레이션 로직을 추가해야 할 수 있습니다:
- 기존 한글 컬럼명 데이터를 새 영문 컬럼명으로 복사
- 기존 컬럼 삭제

### 5단계: 마이그레이션 실행
```bash
python manage.py migrate
```

### 6단계: Serializer 및 Views 수정 (필요시)
Report 모델에서 `company_obj`를 제거했으므로, `serializers.py`와 `views.py`에서 `company_obj` 사용 부분을 `company_code`로 변경해야 할 수 있습니다.

## 주의사항

1. **인덱스 및 제약조건**: 오라클은 인덱스/제약조건 이름이 30자 제한이 있을 수 있습니다. Django가 자동 생성하는 이름이 길 경우 문제가 발생할 수 있습니다.

2. **한글 필드명 사용**: Python 코드에서는 여전히 한글 필드명을 사용할 수 있지만, 실제 DB 쿼리에서는 영문 컬럼명이 사용됩니다.

3. **Serializer 호환성**: 기존 API 응답 형식은 변경되지 않습니다. Python 코드에서는 한글 필드명을 그대로 사용하므로, API 응답도 동일하게 유지됩니다.

4. **데이터 무결성**: 마이그레이션 전에 반드시 데이터 백업을 확인하세요.

## 롤백 방법

마이그레이션을 롤백해야 하는 경우:
```bash
python manage.py migrate myapi <이전_마이그레이션_번호>
```

예: `python manage.py migrate myapi 0021`

## 문제 해결

### 마이그레이션 오류 발생 시
1. 마이그레이션 파일을 확인하고 수동으로 수정
2. 오라클에서 직접 SQL 실행 (필요시)
3. 데이터 마이그레이션 스크립트 작성 (필요시)

### 컬럼명 충돌 오류
- 기존 컬럼명과 새 컬럼명이 충돌하는 경우, 임시 컬럼명을 사용한 후 마이그레이션 수행

