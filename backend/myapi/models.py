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
    ]
    username = models.CharField('아이디', max_length=50, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    employee_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'department', 'employee_number', 'role']

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
            ('기존', '기존'),
            ('신규', '신규'),
            ('이탈', '이탈'),
            ('기타', '기타'),
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
    visitDate = models.DateField(verbose_name='방문일자')
    
    # 회사 관련 (저장 필드)
    company_obj = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports', verbose_name='회사ID')  # 신규 생성 UI 용 참조
    # 회사코드 FK (문자열 PK에 연결)
    company_code = models.ForeignKey(Company, to_field='company_code', db_column='company_code', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_by_code', verbose_name='회사코드')
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
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name='작성일')

    def __str__(self):
        return f"{self.company_name or 'Unknown'} - {self.visitDate}"

    class Meta:
        db_table = 'reports'
        verbose_name = '영업일지'
        verbose_name_plural = '영업일지들'

class CompanyFinancialStatus(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_statuses', verbose_name='회사')
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
        return self.company_name or 'Unknown Income'

class SalesData(models.Model):
    """실제 매출 데이터 모델"""
    매출일자 = models.DateField(verbose_name='매출일자')
    코드 = models.CharField(max_length=50, blank=True, null=True, verbose_name='코드')
    거래처명 = models.CharField(max_length=200, verbose_name='거래처명')
    매출부서 = models.CharField(max_length=100, blank=True, null=True, verbose_name='매출부서')
    매출담당자 = models.CharField(max_length=100, blank=True, null=True, verbose_name='매출담당자')
    유통형태 = models.CharField(max_length=100, blank=True, null=True, verbose_name='유통형태')
    상품코드 = models.CharField(max_length=100, blank=True, null=True, verbose_name='상품코드')
    상품명 = models.CharField(max_length=200, blank=True, null=True, verbose_name='상품명')
    브랜드 = models.CharField(max_length=100, blank=True, null=True, verbose_name='브랜드')
    축종 = models.CharField(max_length=100, blank=True, null=True, verbose_name='축종')
    부위 = models.CharField(max_length=100, blank=True, null=True, verbose_name='부위')
    원산지 = models.CharField(max_length=100, blank=True, null=True, verbose_name='원산지')
    축종_부위 = models.CharField(max_length=100, blank=True, null=True, verbose_name='축종-부위')
    원산지_축종 = models.CharField(max_length=100, blank=True, null=True, verbose_name='원산지')
    등급 = models.CharField(max_length=50, blank=True, null=True, verbose_name='등급')
    Box = models.IntegerField(blank=True, null=True, verbose_name='Box')
    중량_Kg = models.FloatField(blank=True, null=True, verbose_name='중량(Kg)')
    매출단가 = models.IntegerField(blank=True, null=True, verbose_name='매출단가')
    매출금액 = models.BigIntegerField(verbose_name='매출금액')
    매출이익 = models.BigIntegerField(blank=True, null=True, verbose_name='매출이익')
    이익율 = models.FloatField(blank=True, null=True, verbose_name='이익율')
    매입처 = models.CharField(max_length=200, blank=True, null=True, verbose_name='매입 처')
    매입일자 = models.DateField(blank=True, null=True, verbose_name='매입일자')
    재고보유일 = models.IntegerField(blank=True, null=True, verbose_name='재고보유일')
    수입로컬 = models.CharField(max_length=20, blank=True, null=True, verbose_name='수입/로컬')
    이관재고여부 = models.CharField(max_length=20, blank=True, null=True, verbose_name='이관재고 여부')
    담당자 = models.CharField(max_length=100, blank=True, null=True, verbose_name='담당자')
    매입단가 = models.IntegerField(blank=True, null=True, verbose_name='매입단가')
    매입금액 = models.BigIntegerField(blank=True, null=True, verbose_name='매입금액')
    지점명 = models.CharField(max_length=100, blank=True, null=True, verbose_name='지점명')
    매출비고 = models.TextField(blank=True, null=True, verbose_name='매출비고')
    매입비고 = models.TextField(blank=True, null=True, verbose_name='매입비고')
    이력번호 = models.CharField(max_length=100, blank=True, null=True, verbose_name='이력번호')
    BL번호 = models.CharField(max_length=100, blank=True, null=True, verbose_name='B/L번호(도체번호)')
    
    # 연결된 필드 (선택사항)
    company_obj = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_data', verbose_name='연결된 회사')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'sales_data'
        verbose_name = '매출 데이터'
        verbose_name_plural = '매출 데이터들'
        ordering = ['-매출일자', '거래처명']

    def __str__(self):
        return f"{self.거래처명} - {self.매출일자} ({self.매출금액:,}원)"
