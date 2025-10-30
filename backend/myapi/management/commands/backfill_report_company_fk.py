from django.core.management.base import BaseCommand
from django.db import transaction

from myapi.models import Report, Company


class Command(BaseCommand):
    help = 'Backfill Report.company_obj (FK) using stored company_name and city_district.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only print actions, do not write changes')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of reports to process (0 = all)')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        limit = options.get('limit', 0)

        qs = Report.objects.filter(company_obj__isnull=True).exclude(company_name__isnull=True).exclude(company_name='')
        total = qs.count()
        if limit > 0:
            qs = qs[:limit]
        self.stdout.write(f'Target reports: {qs.count()} (of {total})')

        updated = 0
        skipped = 0
        ambiguous = 0
        not_found = 0

        with transaction.atomic():
            for idx, report in enumerate(qs.iterator(), start=1):
                name = (report.company_name or '').strip()
                city = (report.company_city_district or '').strip()

                company = None

                # 1) exact name + city match
                if name and city:
                    candidates = list(Company.objects.filter(company_name=name, city_district=city))
                    if len(candidates) == 1:
                        company = candidates[0]
                    elif len(candidates) > 1:
                        ambiguous += 1

                # 2) exact name match
                if company is None and name:
                    candidates = list(Company.objects.filter(company_name=name))
                    if len(candidates) == 1:
                        company = candidates[0]
                    elif len(candidates) > 1 and city:
                        # try narrowing by city contains
                        city_narrow = [c for c in candidates if (c.city_district or '').strip() == city]
                        if len(city_narrow) == 1:
                            company = city_narrow[0]
                        else:
                            ambiguous += 1

                if company is None:
                    not_found += 1
                    self.stdout.write(f'- Not found: report_id={report.id}, name="{name}", city="{city}"')
                    continue

                if dry_run:
                    self.stdout.write(f'+ Would update report_id={report.id} -> company_code={company.company_code} ({company.company_name})')
                else:
                    # Assign FK (PK is company_code, a string)
                    report.company_obj = company
                    report.save(update_fields=['company_obj'])
                    updated += 1

                if idx % 200 == 0:
                    self.stdout.write(f'Processed {idx}... (updated={updated}, ambiguous={ambiguous}, not_found={not_found})')

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write('Done')
        self.stdout.write(f'- updated: {updated}')
        self.stdout.write(f'- ambiguous: {ambiguous}')
        self.stdout.write(f'- not_found: {not_found}')


