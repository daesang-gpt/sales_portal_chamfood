from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password

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
    # CSV 컬럼과 매핑되는 필드들
    company_name = models.CharField(max_length=200, verbose_name='회사명')
    sales_diary_company_code = models.CharField(max_length=50, blank=True, null=True, verbose_name='영업일지 회사코드')
    company_code_sm = models.CharField(max_length=50, blank=True, null=True, verbose_name='SM 회사코드')
    company_code_sap = models.CharField(max_length=50, blank=True, null=True, verbose_name='SAP 회사코드')
    company_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='회사유형')
    established_date = models.DateField(blank=True, null=True, verbose_name='설립일')
    ceo_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='대표자명')
    address = models.CharField(max_length=500, blank=True, null=True, verbose_name='주소')
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name='담당자')
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='담당자 연락처')
    main_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='대표전화')
    distribution_type_sap = models.CharField(max_length=100, blank=True, null=True, verbose_name='SAP 유통유형')
    industry_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='업종명')
    main_product = models.CharField(max_length=200, blank=True, null=True, verbose_name='주요제품')
    transaction_start_date = models.DateField(blank=True, null=True, verbose_name='거래시작일')
    payment_terms = models.CharField(max_length=200, blank=True, null=True, verbose_name='결제조건')
    customer_classification = models.CharField(max_length=50, blank=True, null=True, verbose_name='고객분류')
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='웹사이트')
    remarks = models.TextField(blank=True, null=True, verbose_name='비고')

    def __str__(self):
        return self.company_name or 'Unknown Company'

    class Meta:
        db_table = 'companies'
        verbose_name = '회사'
        verbose_name_plural = '회사들'

class Report(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')  # 작성자 (User 모델과 연결)
    team = models.CharField(max_length=100)    # 팀명 (User의 department에서 자동 설정)
    visitDate = models.DateField()             # 방문일자
    company = models.CharField(max_length=100) # 회사명 (Company 모델에서 선택하거나 신규 입력)
    company_obj = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')  # Company 모델과 연결 (선택사항)
    type = models.CharField(max_length=20)     # 영업형태 (대면, 전화 등)
    location = models.CharField(max_length=50) # 소재지
    products = models.CharField(max_length=100) # 사용품목
    content = models.TextField()               # 미팅 내용 (이슈사항)
    tags = models.CharField(max_length=200, blank=True)  # 태그 (콤마로 구분된 문자열)
    createdAt = models.DateTimeField(auto_now_add=True) # 작성일

    def __str__(self):
        return f"{self.company} - {self.visitDate}"
