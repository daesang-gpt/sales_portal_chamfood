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
python3 << 'PYTHON_SCRIPT'
import sys
import os

base_file = os.environ.get('DJANGO_ORACLE_BASE', '/opt/sales-portal/backend/venv/lib64/python3.9/site-packages/django/db/backends/oracle/base.py')
intro_file = os.environ.get('DJANGO_ORACLE_INTRO', '/opt/sales-portal/backend/venv/lib64/python3.9/site-packages/django/db/backends/oracle/introspection.py')

# 환경변수에서 가져오기
base_file = sys.argv[1] if len(sys.argv) > 1 else base_file
intro_file = sys.argv[2] if len(sys.argv) > 2 else intro_file

try:
    # base.py 패치
    print("[1/2] base.py 패치 중...")
    with open(base_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # oracledb import가 이미 있는지 확인
    content_str = ''.join(lines)
    if 'import oracledb as Database' in content_str:
        print("  ℹ️  oracledb import 이미 존재")
    else:
        # 52-61번째 줄 근처에서 try-except 블록 찾기
        modified = False
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # try: 다음에 import cx_Oracle이 오는 패턴 찾기
            if i < len(lines) - 1 and 'try:' in line and 'import cx_Oracle as Database' in lines[i+1]:
                print("  ✅ oracledb import 추가 중...")
                new_lines.append(line)  # try: 유지
                new_lines.append("    import oracledb as Database\n")
                new_lines.append("except ImportError:\n")
                new_lines.append("    try:\n")
                new_lines.append("        import cx_Oracle as Database\n")
                # 다음 except ImportError 찾기
                i += 2
                while i < len(lines) and 'except ImportError' not in lines[i]:
                    i += 1
                if i < len(lines):
                    # except ImportError as e: 줄 수정
                    if 'except ImportError as e:' in lines[i]:
                        new_lines.append("    except ImportError as e:\n")
                        i += 1
                        # raise ImproperlyConfigured 줄들 찾기
                        while i < len(lines) and 'raise ImproperlyConfigured' not in lines[i]:
                            i += 1
                        # raise 줄들 수정
                        if i < len(lines):
                            new_lines.append("        raise ImproperlyConfigured(\n")
                            i += 1
                            # 다음 줄들 확인
                            if i < len(lines) and '"Error loading' in lines[i]:
                                new_lines.append('            "Error loading oracledb or cx_Oracle module: %s. "\n')
                                i += 1
                            if i < len(lines) and 'Install oracledb' in lines[i] or '" % e' in lines[i]:
                                new_lines.append('            "Install oracledb (recommended) or cx_Oracle." % e\n')
                                i += 1
                            if i < len(lines) and ')' in lines[i]:
                                new_lines.append("        )\n")
                                i += 1
                modified = True
            else:
                new_lines.append(line)
                i += 1
        
        if modified:
            with open(base_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print("  ✅ oracledb import 추가 완료")
        else:
            # 더 간단한 방법: 직접 문자열 치환
            with open(base_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # try:\n    import cx_Oracle as Database 패턴 찾기
            old_pattern = """try:
    import cx_Oracle as Database
except ImportError as e:
    raise ImproperlyConfigured("Error loading cx_Oracle module: %s" % e)"""
            
            new_pattern = """try:
    import oracledb as Database
except ImportError:
    try:
        import cx_Oracle as Database
    except ImportError as e:
        raise ImproperlyConfigured(
            "Error loading oracledb or cx_Oracle module: %s. "
            "Install oracledb (recommended) or cx_Oracle." % e
        )"""
            
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                with open(base_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✅ oracledb import 추가 완료 (문자열 치환)")
            else:
                print("  ⚠️  패턴을 찾을 수 없습니다. 수동 확인 필요")
                print(f"  파일 내용 일부:\n{content[:500]}")
    
    # Binary 타입 처리 확인 및 수정
    with open(base_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'isinstance(param, (Database.Binary, datetime.timedelta))' in content:
        content = content.replace(
            'elif isinstance(param, (Database.Binary, datetime.timedelta)):',
            '''elif isinstance(param, (bytes, datetime.timedelta)):
            self.force_bytes = param
        elif hasattr(Database, 'Binary') and type(param).__name__ == 'Binary':'''
        )
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ Binary 타입 처리 수정")
    elif 'isinstance(param, bytes)' in content:
        print("  ℹ️  Binary 타입 처리 이미 수정됨")
    
    print("✅ base.py 패치 완료")
    
    # introspection.py 패치
    print("[2/2] introspection.py 패치 중...")
    with open(intro_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # oracledb import가 이미 있는지 확인
    if 'import oracledb as cx_Oracle' in content:
        print("  ℹ️  oracledb import 이미 존재")
    else:
        # import cx_Oracle을 찾아서 교체
        if 'import cx_Oracle' in content:
            # try-except 블록이 이미 있는지 확인
            if 'try:' in content.split('import cx_Oracle')[0][-100:]:
                print("  ℹ️  이미 패치되어 있거나 다른 형식")
            else:
                content = content.replace(
                    'import cx_Oracle',
                    '''try:
    import oracledb as cx_Oracle
except ImportError:
    import cx_Oracle'''
                )
                with open(intro_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("  ✅ oracledb import 추가")
        else:
            print("  ⚠️  import cx_Oracle을 찾을 수 없습니다")
    
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
PYTHON_SCRIPT "$DJANGO_ORACLE_BASE" "$DJANGO_ORACLE_INTRO"
