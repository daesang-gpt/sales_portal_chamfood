#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # .env를 먼저 로드해서 DJANGO_SETTINGS_MODULE 등 환경변수를 manage.py에서도 적용
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        load_dotenv(Path(__file__).resolve().parent / '.env')
    except ImportError:
        pass

    # 프로덕션 설정: RUN_PRODUCTION=1 또는 DJANGO_SETTINGS_MODULE=settings.production
    if os.environ.get('RUN_PRODUCTION', '').lower() in ('1', 'true', 'yes'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()