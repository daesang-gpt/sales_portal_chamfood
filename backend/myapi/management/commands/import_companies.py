import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from myapi.models import Company, CompanyFinancialStatus
from datetime import date


class Command(BaseCommand):
    help = 'CSV 파일에서 회사 데이터를 일괄 업로드합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='업로드할 CSV 파일 경로'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='기존 데이터를 모두 삭제하고 새로 업로드합니다.'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_file}')
            )
            return

        try:
            with transaction.atomic():
                if clear_existing:
                    Company.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING('기존 회사 데이터를 모두 삭제했습니다.')
                    )

                companies_created = 0
                companies_updated = 0

                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    for row in reader:
                        # 날짜 필드 처리
                        established_date = None
                        if row.get('established_date'):
                            try:
                                established_date = datetime.strptime(row['established_date'], '%Y-%m-%d').date()
                            except ValueError:
                                pass

                        transaction_start_date = None
                        if row.get('transaction_start_date'):
                            try:
                                transaction_start_date = datetime.strptime(row['transaction_start_date'], '%Y-%m-%d').date()
                            except ValueError:
                                pass

                        # 기존 회사 확인 (회사명으로)
                        company_name = row.get('company_name', '').strip()
                        if not company_name:
                            continue

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
                        
                        company, created = Company.objects.update_or_create(
                            company_code=company_code,
                            defaults={
                                'company_name': company_name,
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
                            }
                        )

                        if created:
                            companies_created += 1
                            self.stdout.write(
                                f'생성됨: {company_name}'
                            )
                        else:
                            companies_updated += 1
                            self.stdout.write(
                                f'업데이트됨: {company_name}'
                            )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'업로드 완료! 생성: {companies_created}개, 업데이트: {companies_updated}개'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'업로드 중 오류가 발생했습니다: {str(e)}')
            )
            raise 


class Command(BaseCommand):
    help = '예시 회사매출현황 데이터를 추가합니다.'

    def handle(self, *args, **options):
        company_code = 'C0000020'
        company = Company.objects.filter(company_code=company_code).first()
        if not company:
            self.stdout.write(self.style.ERROR(f'회사 코드 {company_code}에 해당하는 회사가 없습니다.'))
            return
        data = [
            # (결산년도, 총자산, 자본금, 자본총계, 매출액, 영업이익, 당기순이익)
            (date(2024,12,31), 948357, 100000, 412939, 10017940, 177331, 175058),
            (date(2023,12,31), 901292, 100000, 237881, 3912333, 39466, 35305),
            (date(2022,12,31), 1093178, 100000, 202576, 5442020, 68757, 61309),
            (date(2021,12,31), 581566, 100000, 141267, 4591711, 41153, 36774),
            (date(2020,12,31), 628810, 100000, 104493, 3174441, 4890, 4493),
        ]
        created = 0
        for fiscal_year, total_assets, capital, total_equity, revenue, operating_income, net_income in data:
            obj, is_created = CompanyFinancialStatus.objects.get_or_create(
                company=company,
                fiscal_year=fiscal_year,
                defaults={
                    'total_assets': total_assets,
                    'capital': capital,
                    'total_equity': total_equity,
                    'revenue': revenue,
                    'operating_income': operating_income,
                    'net_income': net_income,
                }
            )
            if is_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'예시 데이터 {created}건 추가 완료')) 