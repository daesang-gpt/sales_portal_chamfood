import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import User

# 관리자 계정 확인
admin = User.objects.filter(username='admin').first()

if admin:
    print("=== 관리자 계정 정보 ===")
    print(f"아이디: {admin.username}")
    print(f"이름: {admin.name}")
    print(f"부서: {admin.department}")
    print(f"사번: {admin.employee_number}")
    print(f"권한: {admin.role}")
    print(f"활성화: {admin.is_active}")
    print(f"스태프: {admin.is_staff}")
    print(f"슈퍼유저: {admin.is_superuser}")
    
    # 비밀번호 확인 (해시된 상태)
    print(f"비밀번호 설정됨: {'예' if admin.password else '아니오'}")
    
    # 로그인 테스트
    from django.contrib.auth import authenticate
    test_auth = authenticate(username='admin', password='admin1234')
    print(f"인증 테스트: {'성공' if test_auth else '실패'}")
    
else:
    print("관리자 계정이 존재하지 않습니다!")
    
    # 전체 사용자 목록 확인
    all_users = User.objects.all()
    print(f"\n전체 사용자 수: {all_users.count()}")
    for user in all_users:
        print(f"- {user.username} ({user.name}) - {user.role}") 