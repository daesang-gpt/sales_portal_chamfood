#!/bin/bash
# 프로덕션 DB에 마이그레이션 적용
# 사용: ./migrate_production.sh   또는   RUN_PRODUCTION=1 python manage.py migrate
cd "$(dirname "$0")"
export RUN_PRODUCTION=1
python manage.py migrate "$@"
