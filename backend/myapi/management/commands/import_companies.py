import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from myapi.models import Company


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

                        company, created = Company.objects.get_or_create(
                            company_name=company_name,
                            defaults={
                                'sales_diary_company_code': row.get('sales_diary_company_code', '').strip() or None,
                                'company_code_sm': row.get('company_code_sm', '').strip() or None,
                                'company_code_sap': row.get('company_code_sap', '').strip() or None,
                                'company_type': row.get('company_type', '').strip() or None,
                                'established_date': established_date,
                                'ceo_name': row.get('ceo_name', '').strip() or None,
                                'address': row.get('address', '').strip() or None,
                                'contact_person': row.get('contact_person', '').strip() or None,
                                'contact_phone': row.get('contact_phone', '').strip() or None,
                                'main_phone': row.get('main_phone', '').strip() or None,
                                'distribution_type_sap': row.get('distribution_type_sap', '').strip() or None,
                                'industry_name': row.get('industry_name', '').strip() or None,
                                'main_product': row.get('main_product', '').strip() or None,
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
                            # 기존 데이터 업데이트
                            company.sales_diary_company_code = row.get('sales_diary_company_code', '').strip() or company.sales_diary_company_code
                            company.company_code_sm = row.get('company_code_sm', '').strip() or company.company_code_sm
                            company.company_code_sap = row.get('company_code_sap', '').strip() or company.company_code_sap
                            company.company_type = row.get('company_type', '').strip() or company.company_type
                            company.established_date = established_date or company.established_date
                            company.ceo_name = row.get('ceo_name', '').strip() or company.ceo_name
                            company.address = row.get('address', '').strip() or company.address
                            company.contact_person = row.get('contact_person', '').strip() or company.contact_person
                            company.contact_phone = row.get('contact_phone', '').strip() or company.contact_phone
                            company.main_phone = row.get('main_phone', '').strip() or company.main_phone
                            company.distribution_type_sap = row.get('distribution_type_sap', '').strip() or company.distribution_type_sap
                            company.industry_name = row.get('industry_name', '').strip() or company.industry_name
                            company.main_product = row.get('main_product', '').strip() or company.main_product
                            company.transaction_start_date = transaction_start_date or company.transaction_start_date
                            company.payment_terms = row.get('payment_terms', '').strip() or company.payment_terms
                            company.customer_classification = row.get('customer_classification', '').strip() or company.customer_classification
                            company.website = row.get('website', '').strip() or company.website
                            company.remarks = row.get('remarks', '').strip() or company.remarks
                            company.save()
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