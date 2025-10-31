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
                        
                        # company_code 생성 (없으면 자동 생성)
                        company_code = row.get('company_code', '').strip()
                        if not company_code:
                            # 자동 생성 로직
                            from django.db.models import Max
                            last_code = Company.objects.filter(company_code__startswith='C').aggregate(
                                max_code=Max('company_code')
                            )['max_code']
                            if last_code and last_code[1:].isdigit():
                                next_num = int(last_code[1:]) + 1
                            else:
                                next_num = 1
                            company_code = f'C{next_num:07d}'
                        
                        # Company 객체 생성 또는 업데이트
                        company, created = Company.objects.update_or_create(
                            company_code=company_code,
                            defaults={
                                'company_name': row['company_name'],
                                'company_code_sap': row.get('company_code_sap', '').strip() or None,
                                'company_type': row.get('company_type', '').strip() or None,
                                'established_date': established_date,
                                'ceo_name': row.get('ceo_name', '').strip() or None,
                                'head_address': row.get('head_address', '').strip() or row.get('address', '').strip() or None,
                                'processing_address': row.get('processing_address', '').strip() or None,
                                'contact_person': row.get('contact_person', '').strip() or None,
                                'contact_phone': row.get('contact_phone', '').strip() or None,
                                'main_phone': row.get('main_phone', '').strip() or None,
                                'distribution_type_sap': row.get('distribution_type_sap', '').strip() or None,
                                'industry_name': row.get('industry_name', '').strip() or None,
                                'products': row.get('products', '').strip() or row.get('main_product', '').strip() or None,
                                'transaction_start_date': transaction_start_date,
                                'payment_terms': row.get('payment_terms', '').strip() or None,
                                'customer_classification': row.get('customer_classification', '').strip() or None,
                                'website': row.get('website', '').strip() or None,
                                'remarks': row.get('remarks', '').strip() or None,
                                'employee_name': user.name if user and hasattr(user, 'name') else None,
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
