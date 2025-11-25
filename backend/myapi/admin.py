from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm, UserChangeForm
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape
from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib.auth.hashers import make_password
from .models import Company, Report, User, CompanyFinancialStatus
from .signals import create_audit_log

# Register your models here.

class UserAdminForm(UserChangeForm):
    """사용자 편집 폼 - 비밀번호 필드 추가"""
    new_password = forms.CharField(
        label='새 비밀번호',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'vTextField'}),
        help_text='비밀번호를 변경하려면 새 비밀번호를 입력하세요. 비워두면 변경되지 않습니다.'
    )
    confirm_password = forms.CharField(
        label='새 비밀번호 확인',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'vTextField'}),
        help_text='새 비밀번호를 다시 입력하세요.'
    )
    
    class Meta:
        model = User
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError({
                    'confirm_password': '새 비밀번호가 일치하지 않습니다.'
                })
        
        return cleaned_data

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    list_display = ['id', 'username', 'name', 'email', 'department', 'employee_number', 'role', 'is_password_changed']
    list_filter = ['role', 'department', 'is_password_changed']
    search_fields = ['id', 'username', 'name', 'email', 'employee_number']
    ordering = ['id']
    
    # 비밀번호 변경 폼 사용
    change_password_form = AdminPasswordChangeForm
    
    fieldsets = (
        (None, {'fields': ('username',)}),
        ('기본 정보', {
            'fields': ('email', 'name', 'department', 'employee_number', 'role')
        }),
        ('권한', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('비밀번호 변경', {
            'fields': ('new_password', 'confirm_password'),
            'description': '비밀번호를 변경하려면 새 비밀번호를 입력하세요. 이전 비밀번호 확인이 필요하지 않습니다.'
        }),
        ('비밀번호 정보', {
            'fields': ('is_password_changed',)
        }),
        ('기타', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'name', 'department', 'employee_number', 'role'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        사용자 저장 시 비밀번호 변경 처리
        """
        # 권한 변경 감지
        old_role = None
        if change:
            try:
                old_user = User.objects.get(pk=obj.pk)
                old_role = old_user.role
            except User.DoesNotExist:
                pass
        
        # 새 비밀번호가 입력된 경우 처리
        if change and form.cleaned_data.get('new_password'):
            new_password = form.cleaned_data['new_password']
            # 비밀번호를 해시하여 저장
            obj.password = make_password(new_password)
            # 비밀번호가 변경되었으므로 is_password_changed를 False로 설정
            obj.is_password_changed = False
        
        # Django가 자동으로 비밀번호를 해시하여 저장함
        super().save_model(request, obj, form, change)
        
        # 권한 변경 로그 기록
        if change and old_role and old_role != obj.role:
            create_audit_log(
                user=request.user if request.user.is_authenticated else None,
                action_type='permission_change',
                description=f'사용자 {obj.username}의 권한이 {old_role}에서 {obj.role}로 변경되었습니다.',
                request=request if request.user.is_authenticated else None,
                target_user=obj,
                old_value=old_role,
                new_value=obj.role,
            )
    
    def get_urls(self):
        """비밀번호 변경 URL 추가"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.user_change_password),
                name='auth_user_password_change',
            ),
        ]
        return custom_urls + urls
    
    def user_change_password(self, request, id, form_url=''):
        """비밀번호 변경 뷰 오버라이드"""
        user = self.get_object(request, id)
        if user is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
                'name': self.model._meta.verbose_name,
                'key': id,
            })
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                # 비밀번호 변경 후 is_password_changed를 False로 설정
                user.is_password_changed = False
                user.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = _('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect(
                    reverse(
                        '%s:%s_%s_change' % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = self.change_password_form(user)
        
        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})
        
        context = {
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup': (admin.helpers.IS_POPUP_VAR in request.POST or
                        admin.helpers.IS_POPUP_VAR in request.GET),
            'is_popup_var': admin.helpers.IS_POPUP_VAR,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
            **self.admin_site.each_context(request),
        }
        
        request.current_app = self.admin_site.name
        
        return TemplateResponse(
            request,
            'admin/auth/user/change_password.html',
            context,
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

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'visitDate', 'author_name', 'author_department', 'type', 'sales_stage', 'createdAt']
    list_filter = ['type', 'sales_stage', 'visitDate', 'createdAt', 'author_department']
    search_fields = ['company_name', 'content', 'author_name', 'tags']
    ordering = ['-visitDate', '-createdAt']
    readonly_fields = ['createdAt']
    date_hierarchy = 'visitDate'
    list_per_page = 50
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('author', 'author_name', 'author_department', 'visitDate', 'createdAt')
        }),
        ('회사 정보', {
            'fields': ('company_code', 'company_name', 'company_city_district')
        }),
        ('영업 정보', {
            'fields': ('sales_stage', 'type', 'products', 'content', 'tags')
        }),
    )
