import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from myapi.models import User, Report, Company

class Command(BaseCommand):
    help = 'Import sales reports from CSV file'

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
        skipped_count = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외하고 2부터 시작
                    try:
                        # 필수 필드 확인
                        if not row.get('user__username'):
                            raise ValueError('user__username 필드가 누락되었습니다.')
                        
                        if not row.get('visit_date'):
                            raise ValueError('visit_date 필드가 누락되었습니다.')

                        # 작성자 확인
                        try:
                            author = User.objects.get(username=row['user__username'])
                        except User.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'라인 {row_num}: 사용자명 "{row["user__username"]}"을 찾을 수 없습니다. 건너뜁니다.')
                            )
                            skipped_count += 1
                            continue

                        # 날짜 형식 변환
                        try:
                            visit_date = datetime.strptime(row['visit_date'], '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError(f'날짜 형식이 올바르지 않습니다: {row["visit_date"]}')

                        # 회사 코드로 Company 객체 찾기
                        company_obj = None
                        if row.get('company__sales_diary_company_code'):
                            try:
                                company_obj = Company.objects.get(
                                    sales_diary_company_code=row['company__sales_diary_company_code']
                                )
                            except Company.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'라인 {row_num}: 회사 코드 "{row["company__sales_diary_company_code"]}"을 찾을 수 없습니다.')
                                )

                        # created_at 날짜 변환
                        created_at = None
                        if row.get('created_at'):
                            try:
                                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                # created_at이 없거나 형식이 맞지 않으면 현재 시간 사용
                                created_at = datetime.now()

                        # 중복 체크 (동일한 작성자, 방문일, 회사, 영업형태)
                        existing_report = Report.objects.filter(
                            author=author,
                            visitDate=visit_date,
                            company=row.get('company__sales_diary_company_code', ''),
                            type=row.get('sales_type', '')
                        ).first()

                        if existing_report:
                            self.stdout.write(
                                self.style.WARNING(f'라인 {row_num}: 중복된 영업일지가 존재합니다. 건너뜁니다.')
                            )
                            skipped_count += 1
                            continue

                        # 영업일지 생성
                        with transaction.atomic():
                            report = Report.objects.create(
                                author=author,
                                team=author.department,  # 작성자의 부서로 자동 설정
                                visitDate=visit_date,
                                company=row.get('company__sales_diary_company_code', ''),
                                company_obj=company_obj,
                                type=row.get('sales_type', ''),
                                location=row.get('location', ''),
                                products=row.get('main_item', ''),
                                content=row.get('meeting_notes', ''),
                                tags=row.get('tags', ''),
                                createdAt=created_at or datetime.now()
                            )
                        
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'라인 {row_num}: 영업일지 생성 완료 - {author.name} ({visit_date})')
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
        self.stdout.write(self.style.SUCCESS(f'영업일지 일괄 업로드 완료'))
        self.stdout.write(f'성공: {success_count}건')
        self.stdout.write(f'실패: {error_count}건')
        self.stdout.write(f'건너뜀: {skipped_count}건')
        self.stdout.write('='*50) 