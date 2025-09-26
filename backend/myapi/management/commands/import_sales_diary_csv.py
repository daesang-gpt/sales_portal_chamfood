"""
영업일지 CSV 파일을 가져오는 Django 관리 명령어
"""

from django.core.management.base import BaseCommand
from myapi.models import User, Company, Report
import csv
import os
from datetime import datetime


class Command(BaseCommand):
    help = '영업일지 CSV 파일을 데이터베이스에 가져옵니다'

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

        created_count = 0
        updated_count = 0
        error_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # 필수 필드 검증
                        if not row['user__username'].strip():
                            continue
                        
                        # 사용자 찾기
                        try:
                            user = User.objects.get(username=row['user__username'])
                        except User.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'사용자를 찾을 수 없음: {row["user__username"]}')
                            )
                            error_count += 1
                            continue
                        
                        # 회사 찾기 (company__sales_diary_company_code로)
                        company_obj = None
                        if row['company__sales_diary_company_code']:
                            try:
                                company_obj = Company.objects.get(
                                    sales_diary_company_code=row['company__sales_diary_company_code']
                                )
                            except Company.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'회사를 찾을 수 없음: {row["company__sales_diary_company_code"]}')
                                )
                        
                        # 날짜 처리
                        visit_date = None
                        if row['visit_date']:
                            try:
                                visit_date = datetime.strptime(row['visit_date'], '%Y-%m-%d').date()
                            except ValueError:
                                self.stdout.write(
                                    self.style.WARNING(f'잘못된 날짜 형식: {row["visit_date"]}')
                                )
                                continue
                        
                        created_at = None
                        if row['created_at']:
                            try:
                                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                created_at = datetime.now()
                        else:
                            created_at = datetime.now()
                        
                        # Report 객체 생성
                        report = Report.objects.create(
                            author=user,
                            team=user.department,
                            visitDate=visit_date,
                            company=company_obj.company_name if company_obj else '알 수 없는 회사',
                            company_obj=company_obj,
                            type=row['sales_type'] or '기타',
                            location=row['location'] or '',
                            products=row['main_item'] or '',
                            content=row['meeting_notes'] or '',
                            tags=row['tags'] or '',
                            createdAt=created_at,
                        )
                        
                        created_count += 1
                        if created_count % 50 == 0:
                            self.stdout.write(f'✓ {created_count}개 영업일지 생성됨...')
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'행 {row_num} 처리 오류: {e}')
                        )
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'CSV 파일 읽기 오류: {e}')
            )
            return

        self.stdout.write('\n=== 결과 ===')
        self.stdout.write(f'생성된 영업일지: {created_count}개')
        self.stdout.write(f'오류: {error_count}개')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n영업일지 가져오기가 완료되었습니다!')
            )
