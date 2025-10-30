from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Backfill REPORTS.COMPANY_CODE (numeric FK to COMPANIES.ID) using existing COMPANY_OBJ_ID (string code) and name/city heuristics.'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # 1) Fill by joining company_obj_id (string code) -> companies.id
            self.stdout.write('Step 1: Join by company_obj_id to companies.company_code')
            sql1 = """
                UPDATE "REPORTS" r
                SET r."COMPANY_CODE" = (
                    SELECT c."ID" FROM "COMPANIES" c WHERE c."COMPANY_CODE" = r."COMPANY_OBJ_ID"
                )
                WHERE r."COMPANY_CODE" IS NULL AND r."COMPANY_OBJ_ID" IS NOT NULL
            """
            cursor.execute(sql1)
            self.stdout.write(f'  - Updated (by object join): {cursor.rowcount}')

            # 2) Fill by exact name + city match where unique
            self.stdout.write('Step 2: Match by company_name + city_district (unique only)')
            sql2 = """
                MERGE INTO "REPORTS" r USING (
                    SELECT r2."ID" AS rid, c."ID" AS cid
                    FROM "REPORTS" r2
                    JOIN "COMPANIES" c ON c."COMPANY_NAME" = r2."COMPANY_NAME" AND NVL(c."CITY_DISTRICT", '') = NVL(r2."COMPANY_CITY_DISTRICT", '')
                    WHERE r2."COMPANY_CODE" IS NULL AND r2."COMPANY_NAME" IS NOT NULL
                ) m ON (r."ID" = m.rid)
                WHEN MATCHED THEN UPDATE SET r."COMPANY_CODE" = m.cid
            """
            cursor.execute(sql2)
            self.stdout.write(f'  - Updated (by name+city): {cursor.rowcount}')

        self.stdout.write('Done.')


