"""
고객 구분 자동 업데이트를 위한 cron 작업 함수
"""
from django.core.management import call_command


def update_customer_classifications():
    """
    매일 실행되는 cron 작업으로 모든 회사의 고객 구분을 자동 업데이트합니다.
    """
    call_command('update_customer_classifications')

