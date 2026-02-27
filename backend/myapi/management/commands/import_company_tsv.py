"""
회사 TSV 파일 임포트 커맨드
사용법: python manage.py import_company_tsv company_db.tsv
"""
from django.core.management.base import BaseCommand
import csv
from datetime import datetime
from myapi.models import Company, User
from django.utils.dateparse import parse_date


class Command(BaseCommand):
    help = 'TSV 파일에서 회사 데이터를 임포트합니다'

    def add_arguments(self, parser):
        parser.add_argument('tsv_file', type=str, help='임포트할 TSV 파일 경로')

    def handle(self, *args, **options):
        tsv_file = options['tsv_file']
        
        # 기존 회사 데이터 삭제 (외래키 제약 조건 처리)
        self.stdout.write(self.style.WARNING('기존 회사 데이터를 삭제 중입니다...'))
        try:
            from django.db import connection, transaction
            
            with connection.cursor() as cursor:
                # 먼저 외래키 제약 조건을 확인하고 처리
                # CompanyFinancialStatus 데이터 삭제
                try:
                    cursor.execute('DELETE FROM COMPANY_FINANCIAL_STATUS')
                    self.stdout.write(f'  - COMPANY_FINANCIAL_STATUS 데이터 삭제 완료')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  - COMPANY_FINANCIAL_STATUS 삭제 스킵: {e}'))
                
                # SalesData 데이터 삭제 (Company를 참조)
                try:
                    cursor.execute('DELETE FROM SALES_DATA')
                    self.stdout.write(f'  - SALES_DATA 데이터 삭제 완료')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  - SALES_DATA 삭제 스킵: {e}'))
                
                # Report의 company_obj 참조 제거 (SET_NULL 처리)
                try:
                    from myapi.models import Report
                    Report.objects.filter(company_obj__isnull=False).update(company_obj=None)
                    self.stdout.write(f'  - Report의 company_obj 참조 제거 완료')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  - Report 참조 제거 스킵: {e}'))
                
                # 직접 SQL로 Company 데이터 삭제
                try:
                    # 먼저 삭제할 레코드 개수 확인 (간단한 COUNT 쿼리)
                    cursor.execute('SELECT COUNT(*) FROM COMPANIES')
                    row = cursor.fetchone()
                    count_before = row[0] if row and len(row) > 0 else 0
                    
                    # Company 데이터 삭제
                    cursor.execute('DELETE FROM COMPANIES')
                    
                    # 삭제된 개수는 rowcount로 확인할 수 없으므로 위의 count_before 사용
                    connection.commit()
                    
                    self.stdout.write(self.style.SUCCESS(f'  - SQL로 기존 회사 데이터 삭제 완료 ({count_before}개 삭제됨)'))
                        
                except Exception as e:
                    connection.rollback()
                    # 에러가 발생해도 계속 진행 (기존 데이터가 남아있을 수 있음)
                    self.stdout.write(self.style.WARNING(f'  - SQL 삭제 중 오류 발생: {e}'))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'기존 데이터 삭제 중 오류 발생: {e}'))
            self.stdout.write(self.style.ERROR('삭제 실패로 인해 임포트를 중단합니다.'))
            return
        
        # TSV 파일 읽기
        self.stdout.write(self.style.SUCCESS(f'TSV 파일 읽기 시작: {tsv_file}'))
        
        with open(tsv_file, 'r', encoding='utf-8') as f:
            # TSV 리더 생성 (탭 구분)
            reader = csv.DictReader(f, delimiter='\t')
            
            created_count = 0
            error_count = 0
            
            for row_num, row in enumerate(reader, start=2):  # 헤더는 1번째 줄
                try:
                    def _v(key, default=''):
                        """행에서 안전하게 값 추출"""
                        return row.get(key, default or '').strip() or None

                    def _date(key):
                        """날짜 파싱 (YYYY.MM.DD, YYYY-MM-DD 지원)"""
                        raw = row.get(key, '').strip()
                        if not raw or raw in ('0000.00.00', ''):
                            return None
                        try:
                            return parse_date(raw.replace('.', '-'))
                        except Exception:
                            return None

                    def _int(key):
                        """정수 파싱"""
                        raw = row.get(key, '').strip()
                        if not raw:
                            return None
                        try:
                            return int(float(raw.replace(',', '')))
                        except Exception:
                            return None

                    # TSV 코드 컬럼 → company_code / company_code_erp
                    company_code = _v('코드')
                    if not company_code:
                        self.stdout.write(self.style.WARNING(f'라인 {row_num}: 코드가 없어 스킵합니다.'))
                        error_count += 1
                        continue

                    company_name = _v('거래처명') or _v('거래처상호')
                    if not company_name:
                        self.stdout.write(self.style.WARNING(f'라인 {row_num}: 거래처명이 없어 스킵합니다.'))
                        error_count += 1
                        continue

                    # 매입/매출 Y/N 컬럼 → erp_code_type
                    is_매입 = str(row.get('매입', '') or '').strip().upper() in ('Y', '예', '1', 'TRUE')
                    is_매출 = str(row.get('매출', '') or '').strip().upper() in ('Y', '예', '1', 'TRUE')
                    if is_매입 and is_매출:
                        erp_code_type = '매입매출'
                    elif is_매입:
                        erp_code_type = '매입'
                    elif is_매출:
                        erp_code_type = '매출'
                    else:
                        erp_code_type = None

                    company = Company.objects.create(
                        company_code=company_code,
                        company_code_erp=company_code,
                        company_name=company_name,
                        tax_id=_v('사업자번호'),
                        ceo_name=_v('대표자성명'),
                        head_address=_v('본사주소'),
                        main_phone=_v('본사전화번호'),
                        industry_name=_v('업태') or _v('업종분류'),
                        products=_v('주생산품목명'),
                        remarks=_v('비고'),
                        company_type=_v('개인법인구분'),
                        payment_terms=_v('결재방법'),
                        contact_person=_v('업체담당'),
                        contact_phone=_v('담당자전화'),
                        employee_name=_v('자사담당'),
                        registration_date=_date('등록일자'),
                        purchase_unit_price=_int('매입단가'),
                        sale_unit_price=_int('매출단가'),
                        erp_code_type=erp_code_type,
                        customer_classification='신규',
                    )

                    created_count += 1

                    if created_count % 100 == 0:
                        self.stdout.write(f'진행 중... {created_count}개 회사 생성됨')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'라인 {row_num}: 오류 발생 - {str(e)}'))
                    error_count += 1
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'\n임포트 완료!'))
        self.stdout.write(self.style.SUCCESS(f'생성된 회사: {created_count}개'))
        self.stdout.write(self.style.WARNING(f'오류 발생: {error_count}개'))

