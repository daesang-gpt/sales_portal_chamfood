from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from myapi.models import User


class Command(BaseCommand):
    help = '관리자 제외 사용자 비밀번호를 아이디와 동일하게 변경합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='관리자 아이디 (제외할 계정, 기본값: admin)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경 없이 어떤 사용자가 변경될지만 표시',
        )

    def handle(self, *args, **options):
        admin_username = options['username']
        dry_run = options['dry_run']
        
        # 관리자 계정 제외
        users = User.objects.exclude(username=admin_username)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN 모드 (실제 변경 없음) ==='))
        
        updated_count = 0
        failed_count = 0
        
        for user in users:
            try:
                if dry_run:
                    self.stdout.write(f'[예정] {user.username} ({user.name}) - 비밀번호: {user.username}')
                else:
                    user.set_password(user.username)
                    user.is_password_changed = False  # 최초 로그인 강제
                    user.save()
                    
                    # 인증 테스트
                    test_auth = authenticate(username=user.username, password=user.username)
                    if test_auth:
                        self.stdout.write(self.style.SUCCESS(f'[OK] {user.username} ({user.name}) - 비밀번호 변경 완료'))
                        updated_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f'[FAIL] {user.username} ({user.name}) - 인증 테스트 실패'))
                        failed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[ERROR] {user.username} ({user.name}) - 오류: {str(e)}'))
                failed_count += 1
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n=== 완료 ==='))
            self.stdout.write(f'성공: {updated_count}명')
            self.stdout.write(f'실패: {failed_count}명')
        else:
            self.stdout.write(f'\n총 {users.count()}명의 사용자가 변경될 예정입니다.')

