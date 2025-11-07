from django.core.management.base import BaseCommand
from django.db import transaction
from myapi.models import Company


class Command(BaseCommand):
    help = '모든 회사의 고객 구분을 자동으로 계산하여 업데이트합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-code',
            type=str,
            help='특정 회사 코드만 업데이트합니다.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='상세한 진행 상황을 출력합니다.',
        )

    def handle(self, *args, **options):
        company_code = options.get('company_code')
        verbose = options.get('verbose', False)

        # 업데이트할 회사 쿼리셋
        if company_code:
            companies = Company.objects.filter(company_code=company_code)
            if not companies.exists():
                self.stdout.write(
                    self.style.ERROR(f'회사 코드 "{company_code}"를 찾을 수 없습니다.')
                )
                return
        else:
            companies = Company.objects.all()

        total_count = companies.count()
        if total_count == 0:
            self.stdout.write(self.style.WARNING('업데이트할 회사가 없습니다.'))
            return

        self.stdout.write(
            self.style.SUCCESS(f'총 {total_count}개의 회사 고객 구분을 업데이트합니다...')
        )

        updated_count = 0
        error_count = 0

        # 배치 업데이트를 위해 트랜잭션 사용
        with transaction.atomic():
            for idx, company in enumerate(companies.iterator(chunk_size=100), 1):
                try:
                    # 고객 구분 자동 계산
                    old_classification = company.customer_classification
                    new_classification = company.calculate_customer_classification()
                    
                    # 변경사항이 있으면 업데이트
                    if old_classification != new_classification:
                        company.customer_classification = new_classification
                        company.save(update_fields=['customer_classification'])
                        updated_count += 1
                        
                        if verbose:
                            self.stdout.write(
                                f'[{idx}/{total_count}] {company.company_code} ({company.company_name}): '
                                f'{old_classification or "NULL"} -> {new_classification}'
                            )
                    else:
                        if verbose:
                            self.stdout.write(
                                f'[{idx}/{total_count}] {company.company_code} ({company.company_name}): '
                                f'변경 없음 ({new_classification})'
                            )
                    
                    # 진행 상황 출력 (100개마다)
                    if idx % 100 == 0:
                        self.stdout.write(
                            f'진행 상황: {idx}/{total_count} ({idx*100//total_count}%)'
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'[{idx}/{total_count}] {company.company_code} 업데이트 실패: {str(e)}'
                        )
                    )

        # 결과 요약
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('업데이트 완료'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'총 처리 건수: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'업데이트된 건수: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'오류 발생 건수: {error_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

