"""
CSV 파일에서 참조되는 사용자들을 생성하는 Django 관리 명령어
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapi.models import User
import csv
import os


class Command(BaseCommand):
    help = 'CSV 파일에서 참조되는 사용자들을 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='SalesDiary-2025-07-15.csv',
            help='CSV 파일 경로 (기본값: SalesDiary-2025-07-15.csv)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_file}')
            )
            return

        # CSV에서 사용자명 추출
        users_in_csv = set()
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # 헤더 스킵
                
                for row in reader:
                    if len(row) > 1 and row[1]:  # user__username 컬럼
                        users_in_csv.add(row[1])
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'CSV 파일 읽기 오류: {e}')
            )
            return

        self.stdout.write(f'CSV에서 발견된 사용자: {len(users_in_csv)}명')
        
        # 사용자 생성
        created_count = 0
        existing_count = 0
        
        for username in sorted(users_in_csv):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'name': f'사용자 {username}',
                    'department': '영업팀',
                    'employee_number': username,
                    'role': 'user',
                    'password': make_password('temp123!'),  # 임시 비밀번호
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 사용자 생성: {username}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- 이미 존재: {username}')
                )

        self.stdout.write('\n=== 결과 ===')
        self.stdout.write(f'생성된 사용자: {created_count}명')
        self.stdout.write(f'기존 사용자: {existing_count}명')
        self.stdout.write(f'총 사용자: {created_count + existing_count}명')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n사용자 생성이 완료되었습니다!')
            )
            self.stdout.write(
                self.style.WARNING('임시 비밀번호: temp123!')
            )
