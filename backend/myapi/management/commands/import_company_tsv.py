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
                    # 날짜 필드 파싱
                    established_date = None
                    if row.get('설립일') and row['설립일'].strip():
                        try:
                            established_date = parse_date(row['설립일'].strip())
                        except:
                            pass
                    
                    code_create_date = None
                    if row.get('코드생성일') and row['코드생성일'].strip():
                        try:
                            code_create_date = parse_date(row['코드생성일'].strip())
                        except:
                            pass
                    
                    transaction_start_date = None
                    if row.get('거래시작일') and row['거래시작일'].strip():
                        try:
                            transaction_start_date = parse_date(row['거래시작일'].strip())
                        except:
                            pass
                    
                    # User 찾기 (employee_name으로)
                    user = None
                    if row.get('영업 사원') and row['영업 사원'].strip():
                        employee_name = row['영업 사원'].strip()
                        user = User.objects.filter(name=employee_name).first()
                    
                    # SAP코드여부 처리 (매입, 매출, 매입매출 또는 빈 값)
                    sap_code_type_raw = row.get('SAP코드여부', '').strip()
                    sap_code_type = None
                    if sap_code_type_raw:
                        # 유효한 값인지 확인: 매입, 매출, 매입매출 중 하나
                        valid_values = ['매입', '매출', '매입매출']
                        if sap_code_type_raw in valid_values:
                            sap_code_type = sap_code_type_raw
                        # 매입매출은 그대로 저장 (프론트엔드에서 두 체크박스 모두 체크로 처리)
                    
                    # 회사 코드가 없으면 스킵
                    company_code = row.get('회사코드', '').strip()
                    if not company_code:
                        self.stdout.write(self.style.WARNING(f'라인 {row_num}: 회사코드가 없어 스킵합니다.'))
                        error_count += 1
                        continue
                    
                    # 회사명이 없으면 스킵
                    company_name = row.get('회사명', '').strip()
                    if not company_name:
                        self.stdout.write(self.style.WARNING(f'라인 {row_num}: 회사명이 없어 스킵합니다.'))
                        error_count += 1
                        continue
                    
                    # Company 생성
                    company = Company.objects.create(
                        company_code=company_code,
                        company_name=company_name,
                        customer_classification=row.get('고객분류', '').strip() or None,
                        company_type=row.get('회사유형', '').strip() or None,
                        tax_id=row.get('사업자등록번호', '').strip() or None,
                        established_date=established_date,
                        ceo_name=row.get('대표자명', '').strip() or None,
                        head_address=row.get('본사 주소', '').strip() or None,
                        city_district=row.get('시/구', '').strip() or None,
                        processing_address=row.get('공장 주소', '').strip() or None,
                        main_phone=row.get('대표전화', '').strip() or None,
                        industry_name=row.get('업종명', '').strip() or None,
                        products=row.get('주요제품', '').strip() or None,
                        website=row.get('웹사이트', '').strip() or None,
                        remarks=row.get('참고사항', '').strip() or None,
                        sap_code_type=sap_code_type,
                        company_code_sap=row.get('SAP거래처코드', '').strip() or None,
                        biz_code=row.get('사업', '').strip() or None,
                        biz_name=row.get('사업부', '').strip() or None,
                        department_code=row.get('지점/팀', '').strip() or None,
                        department=row.get('팀명', '').strip() or None,
                        employee_number=row.get('사원번호', '').strip() or None,
                        employee_name=row.get('영업 사원', '').strip() or None,
                        distribution_type_sap_code=row.get('유통형태코드', '').strip() or None,
                        distribution_type_sap=row.get('유통형태', '').strip() or None,
                        contact_person=row.get('거래처 담당자', '').strip() or None,
                        contact_phone=row.get('담당자 연락처', '').strip() or None,
                        code_create_date=code_create_date,
                        transaction_start_date=transaction_start_date,
                        payment_terms=row.get('결제조건', '').strip() or None,
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

