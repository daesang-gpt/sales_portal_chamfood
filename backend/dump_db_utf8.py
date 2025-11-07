#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 덤프 생성 스크립트 (인코딩 문제 해결)
"""
import os
import sys
import json
import django

# 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django.setup()

from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
import datetime

def dump_model(model_name, output_file):
    """단일 모델을 덤프합니다."""
    try:
        output = StringIO()
        call_command('dumpdata', model_name, indent=2, stdout=output, skip_checks=True)
        data = output.getvalue()
        
        if data.strip():
            # JSON 파싱하여 유효성 확인
            json_data = json.loads(data)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✅ {model_name} 덤프 완료: {output_file}")
            return True
        else:
            print(f"⚠️ {model_name} 데이터가 없습니다.")
            return False
    except CommandError as e:
        print(f"❌ {model_name} 덤프 실패: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ {model_name} JSON 파싱 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ {model_name} 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def merge_json_files(files, output_file):
    """여러 JSON 파일을 하나로 병합합니다."""
    all_data = []
    for file_path in files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_data.extend(data)
                    else:
                        all_data.append(data)
            except Exception as e:
                print(f"⚠️ 파일 병합 실패 ({file_path}): {e}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 병합 완료: {output_file}")

if __name__ == '__main__':
    # 타임스탬프 생성
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 출력 디렉토리 확인
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db_dumps')
    os.makedirs(output_dir, exist_ok=True)
    
    # 각 모델을 개별적으로 덤프
    models = [
        'myapi.User',
        'myapi.Company',
        'myapi.Report',
        'myapi.CompanyFinancialStatus',
        'myapi.SalesData'
    ]
    
    temp_files = []
    for model in models:
        temp_file = os.path.join(output_dir, f'temp_{model.replace(".", "_")}_{timestamp}.json')
        if dump_model(model, temp_file):
            temp_files.append(temp_file)
    
    # 모든 파일을 하나로 병합
    if temp_files:
        final_file = os.path.join(output_dir, f'db_dump_{timestamp}.json')
        merge_json_files(temp_files, final_file)
        
        # 임시 파일 삭제
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        print(f"\n✅ 전체 덤프 완료: {final_file}")
    else:
        print("\n❌ 덤프할 데이터가 없습니다.")

