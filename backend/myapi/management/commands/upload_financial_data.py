import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from myapi.models import Company, CompanyFinancialStatus
from datetime import datetime


class Command(BaseCommand):
    help = 'Upload financial data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the CSV file',
            default='frontend/app/companies/[id]/financial_company.csv'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        self.stdout.write(f'Processing file: {file_path}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        # 통계 변수
        total_rows = 0
        processed_rows = 0
        skipped_rows = 0
        created_companies = 0
        created_financial_data = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # 탭으로 구분된 CSV 읽기
                reader = csv.DictReader(file, delimiter='\t')
                
                for row in reader:
                    total_rows += 1
                    
                    try:
                        # 데이터 검증 및 변환
                        company_code_sap = row['company_code_sap'].strip()
                        company_name = row['company_name'].strip()
                        fiscal_year_str = row['fiscal_year'].strip()
                        
                        if not company_code_sap or not company_name or not fiscal_year_str:
                            self.stdout.write(
                                self.style.WARNING(f'Row {total_rows}: Missing required data, skipping')
                            )
                            skipped_rows += 1
                            continue
                        
                        # 날짜 변환
                        try:
                            fiscal_year = datetime.strptime(fiscal_year_str, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(
                                self.style.WARNING(f'Row {total_rows}: Invalid date format: {fiscal_year_str}')
                            )
                            skipped_rows += 1
                            continue
                        
                        # 숫자 데이터 변환 (쉼표 제거)
                        try:
                            total_assets = int(row['total_assets'].replace(',', '')) if row['total_assets'] else 0
                            capital = int(row['capital'].replace(',', '')) if row['capital'] else 0
                            total_equity = int(row['total_equity'].replace(',', '')) if row['total_equity'] else 0
                            revenue = int(row['revenue'].replace(',', '')) if row['revenue'] else 0
                            operating_income = int(row['operating_income'].replace(',', '')) if row['operating_income'] else 0
                            net_income = int(row['net_income'].replace(',', '')) if row['net_income'] else 0
                        except ValueError as e:
                            self.stdout.write(
                                self.style.WARNING(f'Row {total_rows}: Invalid number format: {e}')
                            )
                            skipped_rows += 1
                            continue
                        
                        if not dry_run:
                            with transaction.atomic():
                                # Company 찾기 또는 생성
                                company, created = Company.objects.get_or_create(
                                    company_code_sap=company_code_sap,
                                    defaults={
                                        'company_name': company_name,
                                        'sales_diary_company_code': company_code_sap,  # 기본값으로 SAP 코드 사용
                                    }
                                )
                                
                                if created:
                                    created_companies += 1
                                    self.stdout.write(f'Created company: {company_name} ({company_code_sap})')
                                
                                # CompanyFinancialStatus 생성 또는 업데이트
                                financial_status, created = CompanyFinancialStatus.objects.get_or_create(
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
                                
                                if not created:
                                    # 기존 데이터 업데이트
                                    financial_status.total_assets = total_assets
                                    financial_status.capital = capital
                                    financial_status.total_equity = total_equity
                                    financial_status.revenue = revenue
                                    financial_status.operating_income = operating_income
                                    financial_status.net_income = net_income
                                    financial_status.save()
                                
                                if created:
                                    created_financial_data += 1
                        
                        processed_rows += 1
                        
                        if processed_rows % 100 == 0:
                            self.stdout.write(f'Processed {processed_rows} rows...')
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {total_rows}: Error processing: {e}')
                        )
                        skipped_rows += 1
                        continue
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error reading file: {e}')
            )
            return
        
        # 결과 출력
        self.stdout.write('\n' + '='*50)
        self.stdout.write('IMPORT SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Total rows in file: {total_rows}')
        self.stdout.write(f'Successfully processed: {processed_rows}')
        self.stdout.write(f'Skipped rows: {skipped_rows}')
        
        if not dry_run:
            self.stdout.write(f'Companies created: {created_companies}')
            self.stdout.write(f'Financial records created: {created_financial_data}')
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
        else:
            self.stdout.write(self.style.WARNING('DRY RUN completed - no data was saved'))
