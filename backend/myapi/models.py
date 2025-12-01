from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password

# 소재지 선택 옵션
LOCATION_CHOICES = [
    ('수도권', '수도권'),
    ('충청권', '충청권'),
    ('강원권', '강원권'),
    ('영남권', '영남권'),
    ('호남권', '호남권'),
    ('기타', '기타'),
]

# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', '관리자'),
        ('user', '사용자'),
        ('viewer', '뷰어'),
    ]
    username = models.CharField('아이디', max_length=50, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    employee_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField('이메일', blank=True, null=True, help_text='비밀번호 찾기 시 사용됩니다.')
    is_password_changed = models.BooleanField('비밀번호 변경 여부', default=False, help_text='최초 로그인 후 비밀번호 변경 여부')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'department', 'employee_number', 'role', 'email']

    def __str__(self):
        return f"{self.name} ({self.username})"

    class Meta:
        db_table = 'users'


class Company(models.Model):
    # 필수 필드
    company_code = models.CharField(max_length=50, unique=True, primary_key=True, verbose_name='회사코드')
    company_name = models.CharField(max_length=200, verbose_name='회사명')
    
    # 기본정보
    customer_classification = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        choices=[
            ('잠재', '잠재'),
            ('신규', '신규'),
            ('기존', '기존'),
            ('이탈', '이탈'),
            ('벤더', '벤더'),
        ],
        verbose_name='고객분류'
    )
    company_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[
            ('개인', '개인'),
            ('법인', '법인'),
        ],
        verbose_name='회사유형'
    )
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='사업자등록번호')
    established_date = models.DateField(blank=True, null=True, verbose_name='설립일')
    ceo_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='대표자명')
    head_address = models.CharField(max_length=500, blank=True, null=True, verbose_name='본사 주소')
    city_district = models.CharField(max_length=100, blank=True, null=True, verbose_name='시/구')
    processing_address = models.CharField(max_length=500, blank=True, null=True, verbose_name='공장 주소')
    main_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='대표전화')
    industry_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='업종명')
    products = models.TextField(blank=True, null=True, verbose_name='주요제품')
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='웹사이트')
    remarks = models.TextField(blank=True, null=True, verbose_name='참고사항')
    
    # SAP정보
    sap_code_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='SAP코드여부')  # 매입, 매출, 매입매출
    company_code_sap = models.CharField(max_length=50, blank=True, null=True, verbose_name='SAP거래처코드')
    biz_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='사업')
    biz_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='사업부')
    department_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='지점/팀')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='팀명')
    employee_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='사원번호')
    employee_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='영업 사원')
    distribution_type_sap_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='유통형태코드')
    distribution_type_sap = models.CharField(max_length=100, blank=True, null=True, verbose_name='유통형태')
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name='거래처 담당자')
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='담당자 연락처')
    code_create_date = models.DateField(blank=True, null=True, verbose_name='코드생성일')
    transaction_start_date = models.DateField(blank=True, null=True, verbose_name='거래시작일')
    payment_terms = models.CharField(max_length=200, blank=True, null=True, verbose_name='결제조건')

    def calculate_customer_classification(self):
        """
        고객 구분을 자동으로 계산하는 메서드
        규칙:
        - 벤더: SAP 코드여부 속성이 매입인 거래처
        - 잠재: SAP 코드가 없는 거래처
        - 신규: SAP 코드가 있고 코드생성일 기준 3개월 이내인 거래처
        - 기존: SAP 코드가 있고 코드생성일 기준 3개월 초과인 거래처
        - 이탈: SAP 코드가 있고, 마지막 거래일이 3개월 초과인 거래처 (거래일 없으면 이탈)
        """
        from datetime import date, timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        
        # 1. 벤더 확인: SAP 코드여부 속성이 매입인 거래처
        if self.sap_code_type == '매입':
            return '벤더'
        
        # 2. 잠재 확인: SAP 코드가 없는 거래처
        if not self.company_code_sap:
            return '잠재'
        
        # 3. 마지막 거래일 조회 (SalesData에서 company_code_sap로 매칭)
        last_transaction = None
        if self.company_code_sap:
            try:
                last_transaction = SalesData.objects.filter(
                    코드=self.company_code_sap
                ).order_by('-매출일자').first()
            except Exception:
                pass
        
        # 4. 코드생성일 기준 신규/기존 판단
        if self.code_create_date:
            days_since_code_creation = (today - self.code_create_date).days
            
            # SAP 코드가 있고 코드생성일 기준 3개월 이내이면 신규
            if days_since_code_creation <= 90:
                return '신규'
            
            # SAP 코드가 있고 코드생성일 기준 3개월 초과이면 기존 또는 이탈
            # 마지막 거래일 확인
            if last_transaction and last_transaction.매출일자:
                days_since_last_transaction = (today - last_transaction.매출일자).days
                # 마지막 거래일이 3개월 초과이면 이탈
                if days_since_last_transaction > 90:
                    return '이탈'
                else:
                    return '기존'
            else:
                # 거래일이 없으면 이탈
                return '이탈'
        else:
            # 코드생성일이 없으면 마지막 거래일만 확인
            if last_transaction and last_transaction.매출일자:
                days_since_last_transaction = (today - last_transaction.매출일자).days
                if days_since_last_transaction > 90:
                    return '이탈'
                else:
                    return '기존'
            else:
                # 거래일이 없으면 이탈
                return '이탈'

    def __str__(self):
        return self.company_name or 'Unknown Company'

    class Meta:
        db_table = 'companies'
        verbose_name = '회사'
        verbose_name_plural = '회사들'

class Report(models.Model):
    # 영업단계 선택 옵션
    SALES_STAGE_CHOICES = [
        ('초기 컨택', '초기 컨택'),
        ('협상 진행(니즈 파악)', '협상 진행(니즈 파악)'),
        ('계약 체결(거래처 등록)', '계약 체결(거래처 등록)'),
        ('납품 관리', '납품 관리'),
        ('관계 유지', '관계 유지'),
    ]
    
    # 영업형태 선택 옵션
    TYPE_CHOICES = [
        ('대면', '대면'),
        ('전화', '전화'),
        ('이메일', '이메일'),
        ('화상', '화상'),
    ]
    
    # 작성자 관련 (저장 필드)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', verbose_name='작성자ID')  # 작성자 (User 모델과 연결)
    author_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='작성자명')  # 작성자명 저장
    author_department = models.CharField(max_length=100, blank=True, null=True, verbose_name='팀명')  # 팀명 저장
    
    # 방문일자
    visitDate = models.DateField(verbose_name='방문일자', db_column='visit_date')
    
    # 회사 관련 (저장 필드) - company_code FK만 사용 (company_obj 제거)
    company_code = models.ForeignKey(Company, to_field='company_code', db_column='company_code', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports', verbose_name='회사코드')
    company_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='회사명')  # 회사명 저장
    company_city_district = models.CharField(max_length=100, blank=True, null=True, verbose_name='소재지(시/구)')  # 소재지 저장
    
    # 영업단계 (신규)
    sales_stage = models.CharField(
        max_length=50,
        choices=SALES_STAGE_CHOICES,
        blank=True,
        null=True,
        verbose_name='영업단계'
    )
    
    # 영업형태
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='영업형태'
    )
    
    # 사용품목
    products = models.TextField(blank=True, null=True, verbose_name='사용품목')
    
    # 미팅 내용
    content = models.TextField(verbose_name='미팅 내용')
    
    # 태그
    tags = models.CharField(max_length=200, blank=True, verbose_name='태그')
    
    # 작성일
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name='작성일', db_column='created_at')

    def __str__(self):
        return f"{self.company_name or 'Unknown'} - {self.visitDate}"

    class Meta:
        db_table = 'reports'
        verbose_name = '영업일지'
        verbose_name_plural = '영업일지들'

class CompanyFinancialStatus(models.Model):
    company = models.ForeignKey(Company, to_field='company_code', on_delete=models.CASCADE, related_name='financial_statuses', verbose_name='회사', db_column='company_code')
    fiscal_year = models.DateField(verbose_name='결산년도')
    total_assets = models.BigIntegerField(verbose_name='총자산')
    capital = models.BigIntegerField(verbose_name='자본금')
    total_equity = models.BigIntegerField(verbose_name='자본총계')
    revenue = models.BigIntegerField(verbose_name='매출액')
    operating_income = models.BigIntegerField(verbose_name='영업이익')
    net_income = models.BigIntegerField(verbose_name='당기순이익')

    class Meta:
        db_table = 'company_financial_status'
        verbose_name = '회사매출현황'
        verbose_name_plural = '회사매출현황들'
        ordering = ['-fiscal_year', 'company']

    def __str__(self):
        try:
            if self.company:
                company_name = self.company.company_name or self.company.company_code
                return f"{company_name} - {self.fiscal_year}"
            return f"Unknown - {self.fiscal_year}"
        except Exception:
            return f"Financial Status - {self.fiscal_year}"

class SalesData(models.Model):
    """실제 매출 데이터 모델"""
    매출일자 = models.DateField(verbose_name='매출일자', db_column='sale_date')
    코드 = models.CharField(max_length=50, blank=True, null=True, verbose_name='코드', db_column='code')
    거래처명 = models.CharField(max_length=200, verbose_name='거래처명', db_column='customer_name')
    매출부서 = models.CharField(max_length=100, blank=True, null=True, verbose_name='매출부서', db_column='sales_dept')
    매출담당자 = models.CharField(max_length=100, blank=True, null=True, verbose_name='매출담당자', db_column='sales_person')
    유통형태 = models.CharField(max_length=100, blank=True, null=True, verbose_name='유통형태', db_column='distribution_type')
    상품코드 = models.CharField(max_length=100, blank=True, null=True, verbose_name='상품코드', db_column='product_code')
    상품명 = models.CharField(max_length=200, blank=True, null=True, verbose_name='상품명', db_column='product_name')
    브랜드 = models.CharField(max_length=100, blank=True, null=True, verbose_name='브랜드', db_column='brand')
    축종 = models.CharField(max_length=100, blank=True, null=True, verbose_name='축종', db_column='livestock_type')
    부위 = models.CharField(max_length=100, blank=True, null=True, verbose_name='부위', db_column='cut_type')
    원산지 = models.CharField(max_length=100, blank=True, null=True, verbose_name='원산지', db_column='origin')
    축종_부위 = models.CharField(max_length=100, blank=True, null=True, verbose_name='축종-부위', db_column='livestock_cut')
    원산지_축종 = models.CharField(max_length=100, blank=True, null=True, verbose_name='원산지', db_column='origin_livestock')
    등급 = models.CharField(max_length=50, blank=True, null=True, verbose_name='등급', db_column='grade')
    Box = models.IntegerField(blank=True, null=True, verbose_name='Box', db_column='box')
    중량_Kg = models.FloatField(blank=True, null=True, verbose_name='중량(Kg)', db_column='WEIGHT_KG')
    매출단가 = models.IntegerField(blank=True, null=True, verbose_name='매출단가', db_column='sale_unit_price')
    매출금액 = models.BigIntegerField(verbose_name='매출금액', db_column='sale_amount')
    매출이익 = models.BigIntegerField(blank=True, null=True, verbose_name='매출이익', db_column='sale_profit')
    이익율 = models.FloatField(blank=True, null=True, verbose_name='이익율', db_column='profit_rate')
    매입처 = models.CharField(max_length=200, blank=True, null=True, verbose_name='매입 처', db_column='purchase_source')
    매입일자 = models.DateField(blank=True, null=True, verbose_name='매입일자', db_column='purchase_date')
    재고보유일 = models.IntegerField(blank=True, null=True, verbose_name='재고보유일', db_column='inventory_days')
    수입로컬 = models.CharField(max_length=20, blank=True, null=True, verbose_name='수입/로컬', db_column='import_local')
    이관재고여부 = models.CharField(max_length=20, blank=True, null=True, verbose_name='이관재고 여부', db_column='transfer_inventory_yn')
    담당자 = models.CharField(max_length=100, blank=True, null=True, verbose_name='담당자', db_column='manager')
    매입단가 = models.IntegerField(blank=True, null=True, verbose_name='매입단가', db_column='purchase_unit_price')
    매입금액 = models.BigIntegerField(blank=True, null=True, verbose_name='매입금액', db_column='purchase_amount')
    지점명 = models.CharField(max_length=100, blank=True, null=True, verbose_name='지점명', db_column='branch_name')
    매출비고 = models.TextField(blank=True, null=True, verbose_name='매출비고', db_column='sale_note')
    매입비고 = models.TextField(blank=True, null=True, verbose_name='매입비고', db_column='purchase_note')
    이력번호 = models.CharField(max_length=100, blank=True, null=True, verbose_name='이력번호', db_column='history_no')
    BL번호 = models.CharField(max_length=100, blank=True, null=True, verbose_name='B/L번호(도체번호)', db_column='bl_number')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'sales_data'
        verbose_name = '매출 데이터'
        verbose_name_plural = '매출 데이터들'
        ordering = ['-매출일자', '거래처명']

    def __str__(self):
        return f"{self.거래처명} - {self.매출일자} ({self.매출금액:,}원)"

class AuditLog(models.Model):
    """접속 기록 및 권한 변경 로그 모델"""
    ACTION_TYPE_CHOICES = [
        ('login', '로그인'),
        ('logout', '로그아웃'),
        ('permission_change', '권한 변경'),
        ('personal_info_access', '개인정보 접근'),
        ('download', '다운로드'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs', verbose_name='사용자')
    username = models.CharField(max_length=50, blank=True, null=True, verbose_name='사용자명')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, verbose_name='액션 타입')
    description = models.TextField(blank=True, null=True, verbose_name='설명')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP 주소')
    user_agent = models.CharField(max_length=500, blank=True, null=True, verbose_name='User Agent')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_audit_logs', verbose_name='대상 사용자')
    old_value = models.CharField(max_length=200, blank=True, null=True, verbose_name='이전 값')
    new_value = models.CharField(max_length=200, blank=True, null=True, verbose_name='새 값')
    resource_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='리소스 타입')
    resource_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='리소스 ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시', db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = '감사 로그'
        verbose_name_plural = '감사 로그들'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.username or 'Unknown'} - {self.created_at}"

class ProspectCompany(models.Model):
    """업체 리스트 모델"""
    INDUSTRY_CHOICES = [
        ('축산물 가공장', '축산물 가공장'),
        ('식품 가공장', '식품 가공장'),
        ('도소매', '도소매'),
    ]
    
    PRIORITY_CHOICES = [
        ('높음', '높음'),
        ('중간', '중간'),
        ('낮음', '낮음'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('거래중', '거래중'),
        ('미거래', '미거래'),
    ]
    
    license_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='인허가정보')
    company_name = models.CharField(max_length=200, verbose_name='업체명')
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        verbose_name='업종'
    )
    ceo_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='대표자')
    location = models.CharField(max_length=500, blank=True, null=True, verbose_name='소재지')
    main_products = models.TextField(blank=True, null=True, verbose_name='주요제품')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='전화번호')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        blank=True,
        null=True,
        verbose_name='우선순위'
    )
    has_transaction = models.CharField(
        max_length=10,
        choices=TRANSACTION_STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name='자사거래'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')
    
    class Meta:
        db_table = 'prospect_companies'
        verbose_name = '업체 리스트'
        verbose_name_plural = '업체 리스트들'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.company_name or 'Unknown Prospect Company'
