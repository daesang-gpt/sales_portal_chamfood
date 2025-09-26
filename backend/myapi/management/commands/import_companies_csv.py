"""
회사 정보 CSV 파일을 가져오는 Django 관리 명령어
"""

from django.core.management.base import BaseCommand
from myapi.models import Company, User
import csv
import os
from datetime import datetime


class Command(BaseCommand):
    help = '회사 정보 CSV 파일을 데이터베이스에 가져옵니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='companies_export.csv',
            help='CSV 파일 경로 (기본값: companies_export.csv)'
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
            with open(csv_file, 'r', encoding='utf-8-sig') as file:  # BOM 처리
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # 필수 필드 검증
                        if not row['company_name'].strip():
                            continue
                        
                        # 날짜 필드 처리
                        established_date = None
                        if row['established_date']:
                            try:
                                established_date = datetime.strptime(row['established_date'], '%Y-%m-%d').date()
                            except ValueError:
                                pass
                        
                        transaction_start_date = None
                        if row['transaction_start_date']:
                            try:
                                transaction_start_date = datetime.strptime(row['transaction_start_date'], '%Y-%m-%d').date()
                            except ValueError:
                                pass
                        
                        # 사용자 연결
                        user = None
                        if row['username']:
                            try:
                                user = User.objects.get(username=row['username'])
                            except User.DoesNotExist:
                                pass
                        
                        # Company 객체 생성 또는 업데이트
                        company, created = Company.objects.update_or_create(
                            sales_diary_company_code=row['sales_diary_company_code'] or None,
                            defaults={
                                'company_name': row['company_name'],
                                'company_code_sm': row['company_code_sm'] or None,
                                'company_code_sap': row['company_code_sap'] or None,
                                'company_type': row['company_type'] or None,
                                'established_date': established_date,
                                'ceo_name': row['ceo_name'] or None,
                                'address': row['address'] or None,
                                'contact_person': row['contact_person'] or None,
                                'contact_phone': row['contact_phone'] or None,
                                'main_phone': row['main_phone'] or None,
                                'distribution_type_sap': row['distribution_type_sap'] or None,
                                'industry_name': row['industry_name'] or None,
                                'main_product': row['main_product'] or None,
                                'transaction_start_date': transaction_start_date,
                                'payment_terms': row['payment_terms'] or None,
                                'customer_classification': row['customer_classification'] or None,
                                'website': row['website'] or None,
                                'remarks': row['remarks'] or None,
                                'username': user,
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(f'✓ 회사 생성: {company.company_name}')
                        else:
                            updated_count += 1
                            self.stdout.write(f'- 회사 업데이트: {company.company_name}')
                            
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
        self.stdout.write(f'생성된 회사: {created_count}개')
        self.stdout.write(f'업데이트된 회사: {updated_count}개')
        self.stdout.write(f'오류: {error_count}개')
        self.stdout.write(f'총 처리: {created_count + updated_count}개')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\n회사 정보 가져오기가 완료되었습니다!')
            )
