#!/bin/bash
# operations.py 파일 직접 수정 스크립트
# 사용법: ./fix_operations.py.sh

set -e

echo "========================================"
echo "operations.py 파일 직접 수정 시작..."
echo "========================================"

cd /opt/sales-portal/backend
source venv/bin/activate

# operations.py 파일 찾기
OPS_FILE=$(find venv -name "operations.py" -path "*/db/backends/oracle/*" ! -path "*/gis/*" | head -1)

if [ -z "$OPS_FILE" ]; then
    echo "❌ operations.py 파일을 찾을 수 없습니다."
    exit 1
fi

echo "발견된 파일: $OPS_FILE"

# 백업 생성
cp "$OPS_FILE" "${OPS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ 백업 생성 완료"

# Python 스크립트로 직접 수정
python3 << PYTHON_SCRIPT
import sys
import re

ops_file = "$OPS_FILE"

try:
    print(f"[1] 파일 읽기: {ops_file}")
    with open(ops_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 문제가 있는 부분 찾기
    if 'except (TypeError, AttributeError):' in content:
        print("[2] 문제 발견: except 블록이 잘못된 위치에 있습니다")
        
        # convert_datefield_value 함수 찾기
        lines = content.split('\n')
        new_lines = []
        i = 0
        skip_until_indent = None
        
        while i < len(lines):
            line = lines[i]
            
            # isinstance(value, Database.Timestamp) 또는 hasattr 패턴 찾기
            if ('isinstance(value, Database.Timestamp)' in line or 
                ('hasattr(Database, "Timestamp")' in line and 'isinstance(value, Database.Timestamp)' in line)) and '#' not in line:
                indent = len(line) - len(line.lstrip())
                print(f"[3] 패턴 발견 (라인 {i+1}): {line.strip()}")
                
                # 원래 라인 주석 처리
                new_lines.append(' ' * indent + '# oracledb 호환성: Database.Timestamp 체크 주석 처리')
                new_lines.append(' ' * indent + '# ' + line.lstrip())
                
                # 다음 줄들 확인
                i += 1
                if i < len(lines):
                    # if 블록 내부 코드 찾기
                    while i < len(lines):
                        current_line = lines[i]
                        current_indent = len(current_line) - len(current_line.lstrip())
                        
                        # 같은 들여쓰기 레벨이면 if 블록 종료
                        if current_line.strip() and current_indent <= indent:
                            break
                        
                        # 내부 코드 주석 처리
                        if current_line.strip():
                            new_lines.append(' ' * indent + '# ' + current_line.lstrip())
                        else:
                            new_lines.append(current_line)
                        i += 1
                    # i는 이미 증가했으므로 continue로 넘어감
                    continue
            
            # hasattr만 있는 경우도 처리 (이전 패치에서 추가된 것)
            if 'hasattr(Database, "Timestamp")' in line and 'isinstance' in line and '#' not in line:
                indent = len(line) - len(line.lstrip())
                print(f"[3] hasattr 패턴 발견 (라인 {i+1}): {line.strip()}")
                
                # 원래 라인 주석 처리
                new_lines.append(' ' * indent + '# oracledb 호환성: Database.Timestamp 체크 주석 처리')
                new_lines.append(' ' * indent + '# ' + line.lstrip())
                
                # 다음 줄들 확인 (if 블록 내부 및 except 블록까지)
                i += 1
                if i < len(lines):
                    # if 블록 내부 코드와 except 블록 찾기
                    while i < len(lines):
                        current_line = lines[i]
                        current_indent = len(current_line) - len(current_line.lstrip())
                        
                        # except 블록도 함께 주석 처리
                        if 'except (TypeError, AttributeError):' in current_line:
                            new_lines.append(' ' * indent + '# ' + current_line.lstrip())
                            i += 1
                            # except 블록 내부도 주석 처리
                            if i < len(lines):
                                except_indent = len(current_line) - len(current_line.lstrip())
                                while i < len(lines):
                                    except_line = lines[i]
                                    except_line_indent = len(except_line) - len(except_line.lstrip())
                                    if except_line.strip() and except_line_indent <= except_indent:
                                        break
                                    if except_line.strip():
                                        new_lines.append(' ' * indent + '# ' + except_line.lstrip())
                                    else:
                                        new_lines.append(except_line)
                                    i += 1
                            break
                        
                        # 같은 들여쓰기 레벨이면 if 블록 종료
                        if current_line.strip() and current_indent <= indent:
                            break
                        
                        # 내부 코드 주석 처리
                        if current_line.strip():
                            new_lines.append(' ' * indent + '# ' + current_line.lstrip())
                        else:
                            new_lines.append(current_line)
                        i += 1
                    continue
            
            # 잘못된 except 블록 제거 (try 블록 없이 except만 있는 경우)
            if 'except (TypeError, AttributeError):' in line and '#' not in line:
                indent = len(line) - len(line.lstrip())
                # 이전 몇 줄 확인하여 try 블록이 있는지 확인
                has_try = False
                for j in range(max(0, len(new_lines)-10), len(new_lines)):
                    if j < len(new_lines):
                        prev_line = new_lines[j]
                        prev_indent = len(prev_line) - len(prev_line.lstrip())
                        if 'try:' in prev_line and prev_indent == indent:
                            has_try = True
                            break
                        # 주석 처리된 if 블록 다음에 오는 except도 처리
                        if '# oracledb 호환성: Database.Timestamp 체크 주석 처리' in prev_line:
                            has_try = False  # 주석 처리된 블록 다음이므로 except도 주석 처리 필요
                            break
                
                if not has_try:
                    # try 블록이 없으면 except 블록 주석 처리
                    print(f"[4] 잘못된 except 블록 발견 (라인 {i+1}): {line.strip()}")
                    new_lines.append(' ' * indent + '# oracledb 호환성: 잘못된 except 블록 제거')
                    new_lines.append(' ' * indent + '# ' + line.lstrip())
                    # 다음 pass나 주석도 주석 처리
                    i += 1
                    if i < len(lines):
                        next_line = lines[i]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        # except 블록 내부 코드 주석 처리
                        while i < len(lines) and (next_indent > indent or not next_line.strip()):
                            if next_line.strip():
                                new_lines.append(' ' * indent + '# ' + next_line.lstrip())
                            else:
                                new_lines.append(next_line)
                            i += 1
                            if i < len(lines):
                                next_line = lines[i]
                                next_indent = len(next_line) - len(next_line.lstrip())
                            else:
                                break
                    continue
            
            new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        # 파일 저장
        with open(ops_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[4] ✅ 파일 수정 완료")
        
        # 문법 검사
        print("[5] Python 문법 검사 중...")
        compile(content, ops_file, 'exec')
        print("✅ 문법 검사 통과!")
        
    else:
        print("ℹ️  except 블록을 찾을 수 없습니다. 이미 수정되었을 수 있습니다.")
        
        # isinstance(value, Database.Timestamp) 체크만 확인
        if 'isinstance(value, Database.Timestamp)' in content:
            if '# isinstance(value, Database.Timestamp)' in content:
                print("✅ 이미 주석 처리되어 있습니다.")
            else:
                print("⚠️  isinstance 체크가 아직 활성화되어 있습니다.")
        else:
            print("✅ Database.Timestamp 체크가 없습니다.")
    
    print("")
    print("========================================")
    print("✅ 수정 완료!")
    print("========================================")
    
except SyntaxError as e:
    print(f"❌ 문법 오류: {e}")
    print(f"   라인 {e.lineno}: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "다음 단계: Django 설정 테스트"
cd /opt/sales-portal/backend
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=settings.production
export SECRET_KEY=your-production-secret-key-here
export ALLOWED_HOSTS=192.168.99.37,dslspdev
export DB_NAME=192.168.99.37:1521/XEPDB1
export DB_USER=salesportal
export DB_PASSWORD=salesportal123
export ORACLE_HOME=/u01/app/oracle/product/19c/db_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib:$LD_LIBRARY_PATH
export PATH=$ORACLE_HOME/bin:$PATH

echo "Django 설정 검사 중..."
python manage.py check --settings=settings.production 2>&1 | head -20

