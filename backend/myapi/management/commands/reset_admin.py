from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from myapi.models import User


class Command(BaseCommand):
    help = '관리자 계정 비밀번호를 재설정합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='admin1234',
            help='설정할 비밀번호 (기본값: admin1234)',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='관리자 아이디 (기본값: admin)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        admin = User.objects.filter(username=username).first()
        
        if admin:
            self.stdout.write(f'{username} 계정을 찾았습니다. 비밀번호를 재설정합니다...')
            
            admin.set_password(password)
            admin.save()
            
            self.stdout.write(self.style.SUCCESS(f'비밀번호가 성공적으로 재설정되었습니다!'))
            self.stdout.write(f'아이디: {username}')
            self.stdout.write(f'비밀번호: {password}')
            
            # 인증 테스트
            test_auth = authenticate(username=username, password=password)
            
            if test_auth:
                self.stdout.write(self.style.SUCCESS('로그인 테스트 성공!'))
                self.stdout.write(f'이름: {test_auth.name}')
                self.stdout.write(f'권한: {test_auth.role}')
            else:
                self.stdout.write(self.style.ERROR('로그인 테스트 실패!'))
        else:
            self.stdout.write(self.style.ERROR(f'{username} 계정을 찾을 수 없습니다!'))

