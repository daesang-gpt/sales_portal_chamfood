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
        via_obj = 0
        via_lookup = 0
        ambiguous = 0
        not_found = 0

        with transaction.atomic():
            for idx, report in enumerate(qs.iterator(), start=1):
                resolved = None

                # 1) Use company_obj if present
                if report.company_obj:
                    resolved = report.company_obj
                    via_obj += 1

                # 2) Lookup by name + city, then by name only
                if resolved is None:
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
                        ambiguous += 1
                    else:
                        not_found += 1

                if resolved and not dry_run:
                    report.company_code = resolved  # to_field company_code
                    report.save(update_fields=['company_code'])
                    updated += 1

                if idx % 200 == 0:
                    self.stdout.write(f'Processed {idx}... (updated={updated})')

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write('Done')
        self.stdout.write(f'- updated: {updated}')
        self.stdout.write(f'- via_obj: {via_obj}, via_lookup: {via_lookup}')
        self.stdout.write(f'- ambiguous: {ambiguous}, not_found: {not_found}')


