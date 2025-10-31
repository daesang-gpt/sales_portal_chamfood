# -*- coding: utf-8 -*-
import os
import sys
import django

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import User

# 관리자 계정 찾기
admin = User.objects.filter(username='admin').first()

if admin:
    print("관리자 계정을 찾았습니다. 비밀번호를 재설정합니다...")
    
    # 비밀번호 재설정
    admin.set_password('admin1234')
    admin.save()
    
    print("비밀번호가 성공적으로 재설정되었습니다!")
    print("아이디: admin")
    print("비밀번호: admin1234")
    
    # 인증 테스트
    from django.contrib.auth import authenticate
    test_auth = authenticate(username='admin', password='admin1234')
    
    if test_auth:
        print("로그인 테스트 성공!")
        print(f"이름: {test_auth.name}")
        print(f"권한: {test_auth.role}")
    else:
        print("로그인 테스트 실패!")
        
else:
    print("관리자 계정을 찾을 수 없습니다!")

