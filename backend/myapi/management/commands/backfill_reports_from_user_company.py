from django.core.management.base import BaseCommand
from django.db import transaction

from myapi.models import Report, User, Company


class Command(BaseCommand):
    help = 'Backfill missing author/team and company display fields on reports from User and Company models.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not write changes, only show what would change')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        updated_author_name = 0
        updated_author_dept = 0
        updated_company_name = 0
        updated_company_loc = 0

        qs = Report.objects.all()
        total = qs.count()
        self.stdout.write(f'Total reports: {total}')

        with transaction.atomic():
            for idx, report in enumerate(qs.iterator(), start=1):
                changed = False

                # Backfill author fields
                if report.author and (not report.author_name or report.author_name.strip() == ''):
                    report.author_name = report.author.name or ''
                    updated_author_name += 1
                    changed = True
                if report.author and (not report.author_department or report.author_department.strip() == ''):
                    report.author_department = report.author.department or ''
                    updated_author_dept += 1
                    changed = True

                # Backfill company display fields using company_obj when available
                if report.company_obj:
                    if not report.company_name or report.company_name.strip() == '':
                        report.company_name = report.company_obj.company_name or ''
                        updated_company_name += 1
                        changed = True
                    if not report.company_city_district or report.company_city_district.strip() == '':
                        report.company_city_district = report.company_obj.city_district or ''
                        updated_company_loc += 1
                        changed = True
                else:
                    # Optional: try exact name match if company_obj is missing and company_name is empty
                    if (not report.company_name or report.company_name.strip() == ''):
                        comp = Company.objects.filter(company_name=report.company_name).first() if report.company_name else None
                        if comp:
                            report.company_name = comp.company_name or ''
                            if not report.company_city_district or report.company_city_district.strip() == '':
                                report.company_city_district = comp.city_district or ''
                                updated_company_loc += 1
                            updated_company_name += 1
                            changed = True

                if changed and not dry_run:
                    report.save(update_fields=['author_name', 'author_department', 'company_name', 'company_city_district'])

                if idx % 500 == 0:
                    self.stdout.write(f'Processed {idx}/{total}...')

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write('\nBackfill complete:')
        self.stdout.write(f'- author_name updated: {updated_author_name}')
        self.stdout.write(f'- author_department updated: {updated_author_dept}')
        self.stdout.write(f'- company_name updated: {updated_company_name}')
        self.stdout.write(f'- company_city_district updated: {updated_company_loc}')


