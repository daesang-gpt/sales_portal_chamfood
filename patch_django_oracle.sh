#!/bin/bash
# 운영서버에서 Django Oracle 백엔드를 oracledb 사용하도록 패치하는 스크립트
# 사용법: ./patch_django_oracle.sh

set -e

echo "========================================"
echo "Django Oracle 백엔드 패치 시작..."
echo "========================================"

# Django Oracle 백엔드 파일 찾기
DJANGO_ORACLE_BASE=$(find /opt/sales-portal/backend/venv -name "base.py" -path "*/oracle/*" 2>/dev/null | head -1)
DJANGO_ORACLE_INTRO=$(find /opt/sales-portal/backend/venv -name "introspection.py" -path "*/oracle/*" 2>/dev/null | head -1)

if [ -z "$DJANGO_ORACLE_BASE" ] || [ -z "$DJANGO_ORACLE_INTRO" ]; then
    echo "❌ Django Oracle 백엔드 파일을 찾을 수 없습니다."
    echo "   base.py: $DJANGO_ORACLE_BASE"
    echo "   introspection.py: $DJANGO_ORACLE_INTRO"
    exit 1
fi

echo "발견된 파일:"
echo "  base.py: $DJANGO_ORACLE_BASE"
echo "  introspection.py: $DJANGO_ORACLE_INTRO"
echo ""

# Python 스크립트로 패치 실행
python3 << PYTHON_SCRIPT
import re
import sys

base_file = "$DJANGO_ORACLE_BASE"
intro_file = "$DJANGO_ORACLE_INTRO"

try:
    # base.py 패치
    print("[1/2] base.py 패치 중...")
    with open(base_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # oracledb import 부분이 이미 수정되어 있는지 확인
    if 'import oracledb as Database' not in content:
        # cx_Oracle import를 oracledb로 변경
        pattern = r'try:\s+import cx_Oracle as Database\s+except ImportError as e:\s+raise ImproperlyConfigured\("Error loading cx_Oracle module: %s" % e\)'
        replacement = '''try:
    import oracledb as Database
except ImportError:
    try:
        import cx_Oracle as Database
    except ImportError as e:
        raise ImproperlyConfigured(
            "Error loading oracledb or cx_Oracle module: %s. "
            "Install oracledb (recommended) or cx_Oracle." % e
        )'''
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("  ✅ oracledb import 추가")
    else:
        print("  ℹ️  oracledb import 이미 존재")
    
    # Binary 타입 처리 수정 (이미 수정되어 있으면 건너뛰기)
    if 'isinstance(param, (Database.Binary, datetime.timedelta))' in content:
        content = content.replace(
            'elif isinstance(param, (Database.Binary, datetime.timedelta)):',
            '''elif isinstance(param, (bytes, datetime.timedelta)):
            self.force_bytes = param
        elif hasattr(Database, 'Binary') and type(param).__name__ == 'Binary':'''
        )
        print("  ✅ Binary 타입 처리 수정")
    elif 'isinstance(param, bytes)' in content and 'isinstance(param, datetime.timedelta)' in content:
        print("  ℹ️  Binary 타입 처리 이미 수정됨")
    
    with open(base_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ base.py 패치 완료")
    
    # introspection.py 패치
    print("[2/2] introspection.py 패치 중...")
    with open(intro_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # oracledb import가 이미 있는지 확인
    if 'import oracledb as cx_Oracle' not in content:
        # import cx_Oracle을 oracledb 우선으로 변경
        if 'import cx_Oracle' in content and 'try:' not in content.split('import cx_Oracle')[0][-50:]:
            content = content.replace(
                'import cx_Oracle',
                '''try:
    import oracledb as cx_Oracle
except ImportError:
    import cx_Oracle'''
            )
            print("  ✅ oracledb import 추가")
        else:
            print("  ℹ️  이미 패치되어 있거나 다른 형식")
    else:
        print("  ℹ️  oracledb import 이미 존재")
    
    with open(intro_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ introspection.py 패치 완료")
    
    print("")
    print("========================================")
    print("✅ 모든 패치 완료!")
    print("========================================")
    
except Exception as e:
    print(f"❌ 패치 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT
