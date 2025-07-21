import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from myapi.models import User

class Command(BaseCommand):
    help = 'Import users from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_file}')
            )
            return

        success_count = 0
        error_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외하고 2부터 시작
                    try:
                        # 필수 필드 확인
                        required_fields = ['username', 'name', 'department', 'employee_number', 'role', 'password']
                        for field in required_fields:
                            if not row.get(field):
                                raise ValueError(f'필수 필드가 누락되었습니다: {field}')

                        # 기존 사용자 확인
                        if User.objects.filter(username=row['username']).exists():
                            self.stdout.write(
                                self.style.WARNING(f'라인 {row_num}: 사용자명 "{row["username"]}"이 이미 존재합니다. 건너뜁니다.')
                            )
                            continue

                        if User.objects.filter(employee_number=row['employee_number']).exists():
                            self.stdout.write(
                                self.style.WARNING(f'라인 {row_num}: 사번 "{row["employee_number"]}"이 이미 존재합니다. 건너뜁니다.')
                            )
                            continue

                        # 사용자 생성
                        user = User.objects.create(
                            username=row['username'],
                            name=row['name'],
                            department=row['department'],
                            employee_number=row['employee_number'],
                            role=row['role'],
                            password=make_password(row['password'])
                        )
                        
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'라인 {row_num}: 사용자 "{user.name}" ({user.username}) 생성 완료')
                        )

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'라인 {row_num}: 오류 - {str(e)}')
                        )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'CSV 파일 읽기 오류: {str(e)}')
            )
            return

        # 결과 요약
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'일괄 업로드 완료'))
        self.stdout.write(f'성공: {success_count}건')
        self.stdout.write(f'실패: {error_count}건')
        self.stdout.write('='*50) 