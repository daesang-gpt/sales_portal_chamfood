from django.contrib import admin
from .models import Company, Report, User, CompanyFinancialStatus

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'name', 'email', 'department', 'employee_number', 'role']
    list_filter = ['role', 'department']
    search_fields = ['id', 'username', 'name', 'email', 'employee_number']
    ordering = ['id']
    fieldsets = (
        ('기본 정보', {
            'fields': ('username', 'email', 'name', 'department', 'employee_number', 'role')
        }),
        ('권한', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('기타', {
            'fields': ('last_login', 'date_joined')
        }),
    )

@admin.register(CompanyFinancialStatus)
class CompanyFinancialStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name_display', 'fiscal_year', 'revenue', 'operating_income', 'net_income', 'total_assets']
    list_filter = ['fiscal_year']  # company 필터 제거 (Oracle 숫자 변환 문제)
    search_fields = []  # 검색 기능 임시 비활성화
    ordering = ['-fiscal_year', 'id']  # company 대신 id로 정렬
    readonly_fields = ['company_id_display']  # 읽기 전용 필드
    # date_hierarchy 제거 (Oracle에서 문제 발생 가능)
    fieldsets = (
        ('기본 정보', {
            'fields': ('company', 'fiscal_year', 'company_id_display')
        }),
        ('재무 정보', {
            'fields': ('total_assets', 'capital', 'total_equity', 'revenue', 'operating_income', 'net_income')
        }),
    )
    list_per_page = 50
    
    def get_queryset(self, request):
        """쿼리셋 최적화 및 안전성 향상"""
        # 기본 쿼리셋만 사용 (JOIN 최소화)
        qs = super().get_queryset(request)
        # select_related 사용하지 않음 (Oracle에서 문제 발생 가능)
        # only()를 사용하여 필요한 필드만 선택
        return qs.only('id', 'company_id', 'fiscal_year', 'total_assets', 'capital', 
                       'total_equity', 'revenue', 'operating_income', 'net_income')
    
    def company_name_display(self, obj):
        """회사명 표시용 메서드"""
        try:
            # company_id를 사용하여 직접 Company 조회 (to_field 문제 회피)
            from django.db import connection
            with connection.cursor() as cursor:
                # cx_Oracle 직접 사용
                try:
                    cx_cursor = cursor.cursor
                    cx_cursor.execute(
                        "SELECT COMPANY_NAME FROM COMPANIES WHERE ID = :1",
                        [obj.company_id]
                    )
                    result = cx_cursor.fetchone()
                    if result:
                        return result[0]
                except Exception:
                    # cx_Oracle 실패 시 Django 방식 시도
                    cursor.execute(
                        "SELECT COMPANY_NAME FROM COMPANIES WHERE ID = %s",
                        [obj.company_id]
                    )
                    result = cursor.fetchone()
                    if result:
                        return result[0]
            return f'ID: {obj.company_id}'
        except Exception:
            return f'ID: {obj.company_id}'
    company_name_display.short_description = '회사명'
    
    def company_id_display(self, obj):
        """Company ID 표시용 메서드"""
        try:
            return obj.company_id
        except:
            return 'N/A'
    company_id_display.short_description = 'Company ID'

admin.site.register(Company)
admin.site.register(Report)
