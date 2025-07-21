import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
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

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외하고 2부터 시작
                    try:
                        # 필수 필드 확인
                        required_fields = ['author_username', 'visitDate', 'company', 'type', 'location', 'products', 'content']
                        for field in required_fields:
                            if not row.get(field):
                                raise ValueError(f'필수 필드가 누락되었습니다: {field}')

                        # 작성자 확인
                        try:
                            author = User.objects.get(username=row['author_username'])
                        except User.DoesNotExist:
                            raise ValueError(f'사용자명 "{row["author_username"]}"을 찾을 수 없습니다.')

                        # 날짜 형식 확인
                        try:
                            visit_date = datetime.strptime(row['visitDate'], '%Y-%m-%d').date()
                        except ValueError:
                            raise ValueError(f'날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식으로 입력해주세요: {row["visitDate"]}')

                        # 회사 확인 (선택사항)
                        company_obj = None
                        if row.get('company_id'):
                            try:
                                company_obj = Company.objects.get(id=row['company_id'])
                            except Company.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'라인 {row_num}: 회사 ID "{row["company_id"]}"을 찾을 수 없습니다. 회사명만 저장합니다.')
                                )

                        # 영업일지 생성
                        report = Report.objects.create(
                            author=author,
                            team=author.department,  # 작성자의 부서로 자동 설정
                            visitDate=visit_date,
                            company=row['company'],
                            company_obj=company_obj,
                            type=row['type'],
                            location=row['location'],
                            products=row['products'],
                            content=row['content'],
                            tags=row.get('tags', '')  # 선택사항
                        )
                        
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'라인 {row_num}: 영업일지 "{report.company}" ({report.visitDate}) 생성 완료')
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