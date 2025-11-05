from django.core.management.base import BaseCommand
from django.db import transaction

from myapi.models import Report, Company


class Command(BaseCommand):
    help = 'Backfill Report.company_code FK using company_obj or stored company_name/city.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int, default=0)

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        limit = options.get('limit', 0)

        qs = Report.objects.filter(company_code__isnull=True)
        total_missing = qs.count()
        if limit > 0:
            qs = qs[:limit]
        self.stdout.write(f'Target (missing company_code): {qs.count()} of {total_missing}')

        updated = 0
        via_lookup = 0
        ambiguous = 0
        not_found = 0

        with transaction.atomic():
            for idx, report in enumerate(qs.iterator(), start=1):
                resolved = None

                # Lookup by name + city, then by name only
                name = (report.company_name or '').strip()
                city = (report.company_city_district or '').strip()
                candidates = []
                
                if name and city:
                    candidates = list(Company.objects.filter(company_name=name, city_district=city))
                if not candidates and name:
                    candidates = list(Company.objects.filter(company_name=name))
                    
                if len(candidates) == 1:
                    resolved = candidates[0]
                    via_lookup += 1
                elif len(candidates) > 1:
                    # 소재지로 좁히기 시도
                    if city:
                        city_narrow = [c for c in candidates if (c.city_district or '').strip() == city]
                        if len(city_narrow) == 1:
                            resolved = city_narrow[0]
                            via_lookup += 1
                        else:
                            ambiguous += 1
                    else:
                        ambiguous += 1
                else:
                    not_found += 1

                if resolved and not dry_run:
                    try:
                        # Oracle에서 FK 업데이트 시 company_code_id를 직접 설정
                        # to_field='company_code'이므로 실제 FK 값은 company_code 문자열
                        report.company_code_id = resolved.company_code
                        report.save(update_fields=['company_code'])
                        updated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'오류 발생 (ID {report.id}): {e}'))
                        not_found += 1

                if idx % 200 == 0:
                    self.stdout.write(f'Processed {idx}... (updated={updated})')

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write('Done')
        self.stdout.write(f'- updated: {updated}')
        self.stdout.write(f'- via_lookup: {via_lookup}')
        self.stdout.write(f'- ambiguous: {ambiguous}, not_found: {not_found}')


