import os
import sys
import traceback

# 환경 변수 설정
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.development'
os.environ['DB_NAME'] = 'localhost:1521/XEPDB1'
os.environ['DB_USER'] = 'salesportal'
os.environ['DB_PASSWORD'] = 'salesportal123'

# Django 설정
import django
django.setup()

# dumpdata 실행
from django.core.management import call_command

try:
    call_command(
        'dumpdata',
        'myapi.User',
        'myapi.Company', 
        'myapi.Report',
        'myapi.CompanyFinancialStatus',
        'myapi.SalesData',
        '--indent', '2',
        '--output', '../db_dumps/db_dump_final.json',
        '--skip-checks',
        '--verbosity', '2',
        '--traceback'
    )
    print("Success: Dump created!")
except Exception as e:
    print("Error occurred:")
    traceback.print_exc()
    sys.exit(1)

