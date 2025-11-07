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

if [ -z "$DJANGO_ORACLE_BASE" ]; then
    echo "❌ base.py 파일을 찾을 수 없습니다."
    exit 1
fi

if [ -z "$DJANGO_ORACLE_INTRO" ]; then
    echo "❌ introspection.py 파일을 찾을 수 없습니다."
    exit 1
fi

echo "발견된 파일:"
echo "  base.py: $DJANGO_ORACLE_BASE"
echo "  introspection.py: $DJANGO_ORACLE_INTRO"
echo ""

# Python 스크립트로 패치 실행
python3 << PYTHON_SCRIPT
import sys

base_file = "$DJANGO_ORACLE_BASE"
intro_file = "$DJANGO_ORACLE_INTRO"

try:
    # base.py 패치
    print("[1/2] base.py 패치 중...")
    with open(base_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # oracledb import가 이미 있는지 확인
    if 'import oracledb as Database' in content:
        print("  ℹ️  oracledb import 이미 존재")
    else:
        # 가장 일반적인 패턴: try: 다음에 import cx_Oracle
        # 여러 패턴 시도
        patterns = [
            # 패턴 1: try:\n    import cx_Oracle as Database\nexcept ImportError as e:\n    raise ImproperlyConfigured("Error loading cx_Oracle module: %s" % e)
            (
                """try:
    import cx_Oracle as Database
except ImportError as e:
    raise ImproperlyConfigured("Error loading cx_Oracle module: %s" % e)""",
                """try:
    import oracledb as Database
except ImportError:
    try:
        import cx_Oracle as Database
    except ImportError as e:
        raise ImproperlyConfigured(
            "Error loading oracledb or cx_Oracle module: %s. "
            "Install oracledb (recommended) or cx_Oracle." % e
        )"""
            ),
            # 패턴 2: try:\n    import cx_Oracle as Database\n...
            (
                """try:
    import cx_Oracle as Database""",
                """try:
    import oracledb as Database
except ImportError:
    try:
        import cx_Oracle as Database"""
            ),
        ]
        
        modified = False
        for old_pattern, new_pattern in patterns:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                # except ImportError as e: 부분도 수정 필요
                if 'except ImportError as e:' in content and 'raise ImproperlyConfigured("Error loading cx_Oracle module:' in content:
                    # cx_Oracle 관련 에러 메시지 수정
                    import re
                    content = re.sub(
                        r'raise ImproperlyConfigured\("Error loading cx_Oracle module: %s" % e\)',
                        '''raise ImproperlyConfigured(
            "Error loading oracledb or cx_Oracle module: %s. "
            "Install oracledb (recommended) or cx_Oracle." % e
        )''',
                        content
                    )
                modified = True
                print("  ✅ oracledb import 추가 완료")
                break
        
        if not modified:
            print("  ⚠️  패턴을 찾을 수 없습니다. 직접 수정 시도...")
            # 라인 단위로 직접 수정
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                if 'try:' in lines[i] and i + 1 < len(lines) and 'import cx_Oracle as Database' in lines[i+1]:
                    new_lines.append(lines[i])  # try:
                    new_lines.append("    import oracledb as Database")
                    new_lines.append("except ImportError:")
                    new_lines.append("    try:")
                    new_lines.append("        import cx_Oracle as Database")
                    i += 2
                    # except 블록 건너뛰기
                    while i < len(lines) and not lines[i].strip().startswith('except'):
                        i += 1
                    if i < len(lines) and 'except ImportError as e:' in lines[i]:
                        new_lines.append("    except ImportError as e:")
                        i += 1
                        # raise 줄 찾기
                        while i < len(lines) and 'raise ImproperlyConfigured' not in lines[i]:
                            i += 1
                        if i < len(lines):
                            new_lines.append('        raise ImproperlyConfigured(')
                            i += 1
                            if i < len(lines) and '"Error loading' in lines[i]:
                                new_lines.append('            "Error loading oracledb or cx_Oracle module: %s. "')
                                i += 1
                            if i < len(lines):
                                new_lines.append('            "Install oracledb (recommended) or cx_Oracle." % e')
                                i += 1
                            if i < len(lines) and ')' in lines[i]:
                                new_lines.append('        )')
                                i += 1
                    modified = True
                else:
                    new_lines.append(lines[i])
                    i += 1
            
            if modified:
                content = '\n'.join(new_lines)
                print("  ✅ oracledb import 추가 완료 (라인 단위 수정)")
            else:
                print("  ❌ 패치 실패: 패턴을 찾을 수 없습니다")
                print(f"  파일 내용 일부 (52-62줄):")
                lines = content.split('\n')
                for j in range(max(0, 50), min(len(lines), 63)):
                    print(f"  {j+1:3d}: {lines[j]}")
                sys.exit(1)
        
        with open(base_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
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
        if 'import cx_Oracle' in content and 'try:' not in content.split('import cx_Oracle')[0][-50:]:
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
            print("  ℹ️  이미 패치되어 있거나 다른 형식")
    
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
