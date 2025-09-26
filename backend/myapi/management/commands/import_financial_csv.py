"""
회사 재무 정보 CSV 파일을 가져오는 Django 관리 명령어
"""

from django.core.management.base import BaseCommand
from myapi.models import Company, CompanyFinancialStatus
import csv
import os
from datetime import datetime


class Command(BaseCommand):
    help = '회사 재무 정보 CSV 파일을 데이터베이스에 가져옵니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='company_financial_status_export.csv',
            help='CSV 파일 경로 (기본값: company_financial_status_export.csv)'
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
                        if not row['company'].strip():
                            continue
                        
                        # 회사 찾기
                        try:
                            company = Company.objects.get(company_name=row['company'])
                        except Company.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'회사를 찾을 수 없음: {row["company"]}')
                            )
                            error_count += 1
                            continue
                        
                        # 날짜 처리
                        fiscal_year = None
                        if row['fiscal_year']:
                            try:
                                fiscal_year = datetime.strptime(row['fiscal_year'], '%Y-%m-%d').date()
                            except ValueError:
                                self.stdout.write(
                                    self.style.WARNING(f'잘못된 날짜 형식: {row["fiscal_year"]}')
                                )
                                continue
                        
                        # CompanyFinancialStatus 객체 생성 또는 업데이트
                        financial_status, created = CompanyFinancialStatus.objects.update_or_create(
                            company=company,
                            fiscal_year=fiscal_year,
                            defaults={
                                'total_assets': int(row['total_assets']) if row['total_assets'] else 0,
                                'capital': int(row['capital']) if row['capital'] else 0,
                                'total_equity': int(row['total_equity']) if row['total_equity'] else 0,
                                'revenue': int(row['revenue']) if row['revenue'] else 0,
                                'operating_income': int(row['operating_income']) if row['operating_income'] else 0,
                                'net_income': int(row['net_income']) if row['net_income'] else 0,
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(f'✓ 재무정보 생성: {company.company_name} ({fiscal_year})')
                        else:
                            updated_count += 1
                            self.stdout.write(f'- 재무정보 업데이트: {company.company_name} ({fiscal_year})')
                            
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
        self.stdout.write(f'생성된 재무정보: {created_count}개')
        self.stdout.write(f'업데이트된 재무정보: {updated_count}개')
        self.stdout.write(f'오류: {error_count}개')
        self.stdout.write(f'총 처리: {created_count + updated_count}개')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n회사 재무정보 가져오기가 완료되었습니다!')
            )
