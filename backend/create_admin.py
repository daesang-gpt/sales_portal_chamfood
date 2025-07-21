import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import User

# 관리자 계정 생성
try:
    admin_user = User.objects.create_superuser(
        username='admin',
        password='admin1234',
        name='관리자',
        department='경영지원',
        employee_number='A0001',
        role='admin'
    )
    print(f"관리자 계정이 성공적으로 생성되었습니다!")
    print(f"아이디: {admin_user.username}")
    print(f"비밀번호: admin1234")
    print(f"이름: {admin_user.name}")
    print(f"부서: {admin_user.department}")
    print(f"사번: {admin_user.employee_number}")
    print(f"권한: {admin_user.role}")
except Exception as e:
    print(f"관리자 계정 생성 중 오류 발생: {e}") 