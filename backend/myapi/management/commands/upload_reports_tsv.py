from django.core.management.base import BaseCommand
import pandas as pd
from myapi.models import Report, User, Company
import os


class Command(BaseCommand):
    help = 'TSV 파일에서 영업일지를 업로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            'tsv_file',
            type=str,
            help='업로드할 TSV 파일 경로'
        )
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='기존 영업일지를 모두 삭제하고 새로 업로드합니다',
        )

    def handle(self, *args, **options):
        tsv_file = options['tsv_file']
        delete_existing = options['delete_existing']
        
        if not os.path.exists(tsv_file):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {tsv_file}'))
            return
        
        # 기존 영업일지 삭제
        if delete_existing:
            deleted_count = Report.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'기존 영업일지 {deleted_count}개 삭제됨'))
        else:
            deleted_count = 0
        
        # TSV 파일 읽기
        self.stdout.write(f'TSV 파일 읽기: {tsv_file}')
        try:
            df = pd.read_csv(tsv_file, sep='\t', encoding='utf-8')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'파일 읽기 오류: {str(e)}'))
            return
        
        self.stdout.write(f'총 {len(df)}개 행 발견')
        
        created_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 작성자ID (employee_number로 조회)
                author = None
                author_id_str = str(row['작성자ID']).strip() if pd.notna(row['작성자ID']) else ''
                if author_id_str:
                    try:
                        author = User.objects.get(employee_number=author_id_str)
                    except User.DoesNotExist:
                        errors.append(f"행 {index + 2}: 작성자를 찾을 수 없습니다 (작성자ID: {author_id_str})")
                        continue
                    except User.MultipleObjectsReturned:
                        author = User.objects.filter(employee_number=author_id_str).first()
                
                if not author:
                    errors.append(f"행 {index + 2}: 작성자 정보가 없습니다")
                    continue
                
                # 작성자 정보 저장
                author_name = row['작성자명'] if pd.notna(row.get('작성자명')) else (author.name if author else '')
                author_department = row['팀명'] if pd.notna(row.get('팀명')) else (author.department if author else '')
                
                # 회사ID (company_code로 조회)
                company_obj = None
                company_id_str = str(row['회사ID']).strip() if pd.notna(row['회사ID']) else ''
                if company_id_str:
                    try:
                        company_obj = Company.objects.get(company_code=company_id_str)
                    except Company.DoesNotExist:
                        errors.append(f"행 {index + 2}: 회사를 찾을 수 없습니다 (회사ID: {company_id_str})")
                        continue
                
                # 회사 정보 저장
                company_name = row['회사명'] if pd.notna(row.get('회사명')) else (company_obj.company_name if company_obj else '')
                company_city_district = row.get('소재지(시/구)', '') if pd.notna(row.get('소재지(시/구)', '')) else (company_obj.city_district if company_obj else '')
                
                # 빈 문자열을 None으로 변환 (Oracle 호환성)
                if company_name == '':
                    company_name = None
                if company_city_district == '':
                    company_city_district = None
                
                # 날짜 변환
                visit_date = None
                if pd.notna(row['방문일자']):
                    try:
                        visit_date = pd.to_datetime(row['방문일자']).date()
                    except:
                        errors.append(f"행 {index + 2}: 방문일자 형식이 올바르지 않습니다: {row['방문일자']}")
                        continue
                
                # 작성일 변환 (TSV의 작성일을 createdAt에 사용)
                created_at = None
                if '작성일' in row and pd.notna(row['작성일']) and str(row['작성일']).strip():
                    try:
                        # 날짜를 datetime으로 변환하고 시간을 00:00:00으로 설정
                        date_obj = pd.to_datetime(row['작성일']).date()
                        from django.utils import timezone
                        import datetime
                        created_at = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.min))
                    except Exception as e:
                        # 작성일이 잘못되어도 오류로 처리하지 않고 무시 (방문일자 사용)
                        pass
                
                # 영업단계
                sales_stage = None
                if '영업단계' in row and pd.notna(row['영업단계']) and str(row['영업단계']).strip():
                    sales_stage_str = str(row['영업단계']).strip()
                    valid_stages = [choice[0] for choice in Report.SALES_STAGE_CHOICES]
                    if sales_stage_str in valid_stages:
                        sales_stage = sales_stage_str
                
                # 영업형태 검증
                type_str = str(row['영업형태']).strip() if pd.notna(row['영업형태']) else ''
                valid_types = [choice[0] for choice in Report.TYPE_CHOICES]
                if type_str not in valid_types:
                    errors.append(f"행 {index + 2}: 영업형태가 올바르지 않습니다: {type_str}")
                    continue
                
                # content는 필수이므로 빈 문자열이라도 설정
                content_str = str(row['미팅 내용']).strip() if pd.notna(row.get('미팅 내용')) else ''
                if not content_str:
                    content_str = ' '  # 최소한 공백이라도
                
                # 영업일지 생성 (Django가 자동으로 id를 생성함)
                # 빈 문자열을 None으로 변환 (Oracle 호환성)
                products_value = str(row['사용품목']).strip() if pd.notna(row.get('사용품목')) else None
                if products_value == '':
                    products_value = None
                
                tags_value = str(row['태그']).strip() if pd.notna(row.get('태그')) else None
                if tags_value == '':
                    tags_value = None
                
                author_name_value = author_name if author_name else None
                author_department_value = author_department if author_department else None
                
                report_data = {
                    'author': author,
                    'author_name': author_name_value,
                    'author_department': author_department_value,
                    'visitDate': visit_date,
                    'company_obj': None,  # 일단 None으로 생성한 후 업데이트
                    'company_name': company_name,
                    'company_city_district': company_city_district,
                    'sales_stage': sales_stage,  # null 가능
                    'type': type_str,
                    'products': products_value,
                    'content': content_str,
                    'tags': tags_value,
                }
                
                report = Report.objects.create(**report_data)
                
                # 작성일이 있으면 업데이트 (시간은 00:00:00으로)
                if created_at:
                    report.createdAt = created_at
                    report.save(update_fields=['createdAt'])
                
                # company_obj는 Oracle에서 문자열 primary key ForeignKey가 문제를 일으킬 수 있어
                # 일단 None으로 두고, 필요시 별도 스크립트로 업데이트하거나
                # 데이터베이스 스키마를 확인하여 수정 필요
                
                created_count += 1
                
                if (index + 1) % 100 == 0:
                    self.stdout.write(f'진행: {index + 1}/{len(df)} 행 처리됨')
                    
            except Exception as e:
                error_msg = str(e)
                errors.append(f"행 {index + 2}: {error_msg}")
                # 상세 디버깅 정보 출력
                self.stdout.write(self.style.ERROR(f"행 {index + 2} 오류: {error_msg}"))
                if 'ORA-01722' in error_msg:
                    self.stdout.write(self.style.WARNING(f"  - 데이터: author={author.id if author else None}, visitDate={visit_date}, company_obj={company_obj.company_code if company_obj else None}"))
                    self.stdout.write(self.style.WARNING(f"  - company_name={company_name}, company_city_district={company_city_district}"))
                    self.stdout.write(self.style.WARNING(f"  - type={type_str}, sales_stage={sales_stage}"))
                    self.stdout.write(self.style.WARNING(f"  - products={products_value[:50] if products_value else None}"))
                    import traceback
                    self.stdout.write(self.style.WARNING(f"  - 상세: {traceback.format_exc()}"))
                continue
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'업로드 완료!'))
        self.stdout.write(f'- 생성: {created_count}개')
        if delete_existing:
            self.stdout.write(f'- 삭제: {deleted_count}개')
        if errors:
            self.stdout.write(self.style.WARNING(f'\n오류 발생 ({len(errors)}개):'))
            for error in errors[:20]:
                self.stdout.write(f'  {error}')
        else:
            self.stdout.write(self.style.SUCCESS('- 오류 없음'))
        self.stdout.write('='*50)

