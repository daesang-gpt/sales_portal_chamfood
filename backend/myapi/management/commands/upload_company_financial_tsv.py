import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from myapi.models import Company, CompanyFinancialStatus
from datetime import datetime


class Command(BaseCommand):
    help = '회사 재무정보 TSV 파일을 업로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'tsv_file',
            type=str,
            help='업로드할 TSV 파일 경로'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='데이터를 저장하지 않고 미리보기만 합니다',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='기존 재무정보가 있으면 업데이트합니다',
        )

    def handle(self, *args, **options):
        tsv_file = options['tsv_file']
        dry_run = options['dry_run']
        update_existing = options['update_existing']
        
        if not os.path.exists(tsv_file):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {tsv_file}'))
            return
        
        self.stdout.write(f'TSV 파일 처리 중: {tsv_file}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN 모드 - 데이터가 저장되지 않습니다'))
        
        # 통계 변수
        total_rows = 0
        processed_rows = 0
        skipped_rows = 0
        created_records = 0
        updated_records = 0
        not_found_companies = []
        errors = []
        
        # Company 객체 캐시 (company_code -> Company 객체)
        company_cache = {}
        
        try:
            with open(tsv_file, 'r', encoding='utf-8') as file:
                # 탭으로 구분된 TSV 읽기
                reader = csv.DictReader(file, delimiter='\t')
                
                # 먼저 모든 company_code 수집
                all_company_codes = set()
                rows_data = []  # 나중에 처리할 데이터 저장
                
                # 숫자 데이터 변환 함수
                def parse_int(value):
                    """TSV 파일의 숫자 값을 정수로 변환 (공백, 쉼표 등 제거)"""
                    if value is None:
                        return 0
                    # 문자열로 변환
                    str_value = str(value)
                    # 앞뒤 공백 제거
                    str_value = str_value.strip()
                    # 빈 문자열이면 0 반환
                    if not str_value:
                        return 0
                    # 모든 공백, 쉼표, 탭, 줄바꿈 제거
                    cleaned = str_value.replace(' ', '').replace(',', '').replace('\t', '').replace('\n', '').replace('\r', '')
                    # 빈 문자열이면 0 반환
                    if not cleaned:
                        return 0
                    try:
                        return int(cleaned)
                    except ValueError:
                        # 부동소수점인 경우 정수로 변환 시도
                        try:
                            return int(float(cleaned))
                        except (ValueError, OverflowError):
                            raise ValueError(f"숫자로 변환할 수 없습니다: '{value}'")
                
                # 1단계: 파일 읽기 및 데이터 검증
                for row_num, row in enumerate(reader, start=2):  # 헤더 제외하고 2부터 시작
                    total_rows += 1
                    
                    # 빈 행 건너뛰기
                    if not row or not any(row.values()):
                        skipped_rows += 1
                        continue
                    
                    try:
                        # 데이터 검증 및 변환
                        company_code = row.get('company_code', '').strip()
                        fiscal_year_str = row.get('fiscal_year', '').strip()
                        
                        if not company_code or not fiscal_year_str:
                            skipped_rows += 1
                            errors.append(f'행 {row_num}: 필수 필드(company_code, fiscal_year)가 없습니다')
                            continue
                        
                        # 날짜 변환
                        try:
                            fiscal_year = datetime.strptime(fiscal_year_str, '%Y-%m-%d').date()
                        except ValueError:
                            skipped_rows += 1
                            errors.append(f'행 {row_num}: 잘못된 날짜 형식: {fiscal_year_str} (YYYY-MM-DD 형식이어야 합니다)')
                            continue
                        
                        # 숫자 데이터 변환
                        try:
                            total_assets = parse_int(row.get('total_assets'))
                            capital = parse_int(row.get('capital'))
                            total_equity = parse_int(row.get('total_equity'))
                            revenue = parse_int(row.get('revenue'))
                            operating_income = parse_int(row.get('operating_income'))
                            net_income = parse_int(row.get('net_income'))
                            
                            # 값 검증: 모든 값이 정수인지 확인
                            assert isinstance(total_assets, int), f"total_assets는 정수여야 합니다: {type(total_assets)}"
                            assert isinstance(capital, int), f"capital은 정수여야 합니다: {type(capital)}"
                            assert isinstance(total_equity, int), f"total_equity는 정수여야 합니다: {type(total_equity)}"
                            assert isinstance(revenue, int), f"revenue는 정수여야 합니다: {type(revenue)}"
                            assert isinstance(operating_income, int), f"operating_income은 정수여야 합니다: {type(operating_income)}"
                            assert isinstance(net_income, int), f"net_income은 정수여야 합니다: {type(net_income)}"
                        except (ValueError, TypeError, AssertionError) as e:
                            skipped_rows += 1
                            errors.append(f'행 {row_num}: 숫자 변환 오류: {e}')
                            continue
                        
                        # company_code 수집 및 행 데이터 저장
                        all_company_codes.add(company_code)
                        rows_data.append({
                            'row_num': row_num,
                            'company_code': company_code,
                            'fiscal_year': fiscal_year,
                            'total_assets': total_assets,
                            'capital': capital,
                            'total_equity': total_equity,
                            'revenue': revenue,
                            'operating_income': operating_income,
                            'net_income': net_income
                        })
                    except Exception as e:
                        skipped_rows += 1
                        error_msg = f'행 {row_num}: 처리 중 오류 발생: {str(e)}'
                        errors.append(error_msg)
                        self.stdout.write(self.style.ERROR(error_msg))
                        continue
                
                # 2단계: 모든 Company 존재 여부 확인 및 ID 조회
                if all_company_codes:
                    self.stdout.write(f'Company 존재 여부 확인 및 ID 조회 중... (총 {len(all_company_codes)}개)')
                    # Company.objects를 통해 존재 여부 확인
                    existing_companies = Company.objects.filter(company_code__in=all_company_codes)
                    company_code_set = set(existing_companies.values_list('company_code', flat=True))
                    
                    # 찾을 수 없는 company_code 수집
                    not_found_codes = all_company_codes - company_code_set
                    for code in not_found_codes:
                        if code not in not_found_companies:
                            not_found_companies.append(code)
                    
                    if not dry_run and company_code_set:
                        self.stdout.write(f'Company ID 조회 중... (존재하는 {len(company_code_set)}개)')
                        # 각 Company의 실제 DB ID를 개별 조회 (캐시에 저장)
                        # Oracle 백엔드의 % 포맷팅 문제가 있지만, 한 번만 수행하므로 감수
                        for code in company_code_set:
                            try:
                                with connection.cursor() as id_cursor:
                                    # cx_Oracle 직접 사용 시도
                                    try:
                                        cx_cursor = id_cursor.cursor
                                        cx_cursor.execute(
                                            "SELECT ID FROM COMPANIES WHERE COMPANY_CODE = :1",
                                            [code]
                                        )
                                        id_result = cx_cursor.fetchone()
                                        if id_result:
                                            company_cache[code] = {'id': id_result[0]}
                                    except Exception:
                                        # cx_Oracle 직접 사용 실패 시 Django cursor 사용
                                        id_cursor.execute(
                                            "SELECT ID FROM COMPANIES WHERE COMPANY_CODE = %s",
                                            [code]
                                        )
                                        id_result = id_cursor.fetchone()
                                        if id_result:
                                            company_cache[code] = {'id': id_result[0]}
                            except Exception as id_error:
                                self.stdout.write(self.style.WARNING(f'  Company ID 조회 실패 ({code}): {str(id_error)[:50]}'))
                                # 실패한 경우 나중에 개별 조회로 폴백
                    
                    if not dry_run:
                        self.stdout.write(f'Company ID 캐시 완료: {len(company_cache)}개')
                    if not_found_codes:
                        self.stdout.write(self.style.WARNING(f'찾을 수 없는 Company: {len(not_found_codes)}개'))
                
                # 3단계: 데이터 저장
                if not dry_run:
                    self.stdout.write(f'데이터 저장 중... (총 {len(rows_data)}개 행)')
                
                for row_data in rows_data:
                    row_num = row_data['row_num']
                    company_code = row_data['company_code']
                    fiscal_year = row_data['fiscal_year']
                    total_assets = row_data['total_assets']
                    capital = row_data['capital']
                    total_equity = row_data['total_equity']
                    revenue = row_data['revenue']
                    operating_income = row_data['operating_income']
                    net_income = row_data['net_income']
                    
                    if not dry_run:
                        try:
                            with transaction.atomic():
                                # Company ID 조회 (캐시에서 또는 개별 조회)
                                if company_code not in company_cache:
                                    # 캐시에 없으면 개별 조회 시도
                                    try:
                                        with connection.cursor() as id_cursor:
                                            try:
                                                cx_cursor = id_cursor.cursor
                                                cx_cursor.execute(
                                                    "SELECT ID FROM COMPANIES WHERE COMPANY_CODE = :1",
                                                    [company_code]
                                                )
                                                id_result = cx_cursor.fetchone()
                                                if id_result:
                                                    company_cache[company_code] = {'id': id_result[0]}
                                                else:
                                                    raise ValueError(f"Company ID를 찾을 수 없습니다: {company_code}")
                                            except Exception:
                                                # cx_Oracle 실패 시 Django 방식 시도
                                                id_cursor.execute(
                                                    "SELECT ID FROM COMPANIES WHERE COMPANY_CODE = %s",
                                                    [company_code]
                                                )
                                                id_result = id_cursor.fetchone()
                                                if id_result:
                                                    company_cache[company_code] = {'id': id_result[0]}
                                                else:
                                                    raise ValueError(f"Company ID를 찾을 수 없습니다: {company_code}")
                                    except Exception as lookup_error:
                                        skipped_rows += 1
                                        if company_code not in not_found_companies:
                                            not_found_companies.append(company_code)
                                        errors.append(f'행 {row_num}: Company ID 조회 오류: {str(lookup_error)}')
                                        continue
                                
                                company_id = company_cache[company_code]['id']
                                
                                # CompanyFinancialStatus 생성 또는 업데이트 (company_id 직접 사용)
                                try:
                                    financial_status = CompanyFinancialStatus.objects.get(
                                        company_id=company_id,
                                        fiscal_year=fiscal_year
                                    )
                                    # 기존 레코드 존재
                                    if update_existing:
                                        financial_status.total_assets = total_assets
                                        financial_status.capital = capital
                                        financial_status.total_equity = total_equity
                                        financial_status.revenue = revenue
                                        financial_status.operating_income = operating_income
                                        financial_status.net_income = net_income
                                        financial_status.save()
                                        updated_records += 1
                                    else:
                                        skipped_rows += 1
                                        errors.append(f'행 {row_num}: 이미 존재하는 재무정보입니다 (company_code: {company_code}, fiscal_year: {fiscal_year}). --update-existing 옵션을 사용하세요.')
                                except CompanyFinancialStatus.DoesNotExist:
                                    # 새 레코드 생성 - company_id 직접 사용
                                    try:
                                        financial_status = CompanyFinancialStatus(
                                            company_id=company_id,  # 실제 DB의 ID 컬럼 값 사용
                                            fiscal_year=fiscal_year,
                                            total_assets=total_assets,
                                            capital=capital,
                                            total_equity=total_equity,
                                            revenue=revenue,
                                            operating_income=operating_income,
                                            net_income=net_income
                                        )
                                        financial_status.save()
                                        created_records += 1
                                    except Exception as save_error:
                                        skipped_rows += 1
                                        errors.append(f'행 {row_num}: 저장 오류: {str(save_error)}')
                                        continue
                        except Exception as e:
                            skipped_rows += 1
                            error_detail = f"행 {row_num}: 데이터 저장 오류: {str(e)}"
                            errors.append(error_detail)
                            continue
                    else:
                        # Dry run 모드: Company 존재 여부만 확인
                        if company_code in company_code_set:
                            pass  # 존재함
                        else:
                            skipped_rows += 1
                            if company_code not in not_found_companies:
                                not_found_companies.append(company_code)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'파일 읽기 오류: {e}'))
            return
        
        # 결과 출력
        self.stdout.write('\n' + '='*50)
        self.stdout.write('업로드 결과 요약')
        self.stdout.write('='*50)
        self.stdout.write(f'파일 총 행 수: {total_rows}')
        self.stdout.write(f'성공적으로 처리된 행: {processed_rows}')
        self.stdout.write(f'건너뛴 행: {skipped_rows}')
        
        if not dry_run:
            self.stdout.write(f'생성된 재무정보: {created_records}개')
            if update_existing:
                self.stdout.write(f'업데이트된 재무정보: {updated_records}개')
            self.stdout.write(self.style.SUCCESS('업로드가 완료되었습니다!'))
        else:
            self.stdout.write(self.style.WARNING('DRY RUN 완료 - 데이터가 저장되지 않았습니다'))
        
        # 찾을 수 없는 회사코드 출력
        if not_found_companies:
            self.stdout.write(self.style.WARNING(f'\n찾을 수 없는 회사코드 ({len(not_found_companies)}개):'))
            for code in not_found_companies[:20]:  # 최대 20개만 표시
                self.stdout.write(f'  - {code}')
            if len(not_found_companies) > 20:
                self.stdout.write(f'  ... 외 {len(not_found_companies) - 20}개')
        
        # 오류 출력
        if errors:
            self.stdout.write(self.style.WARNING(f'\n오류 발생 ({len(errors)}개):'))
            for error in errors[:30]:  # 최대 30개만 표시
                self.stdout.write(f'  {error}')
            if len(errors) > 30:
                self.stdout.write(f'  ... 외 {len(errors) - 30}개')
        
        self.stdout.write('='*50)

