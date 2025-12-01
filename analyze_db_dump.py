#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB 덤프 파일 분석 스크립트
각 테이블(모델)별 레코드 개수를 확인합니다.
"""

import json
import sys
from collections import Counter
from pathlib import Path

def analyze_db_dump(file_path):
    """DB 덤프 파일을 분석하여 모델별 레코드 개수를 반환합니다."""
    print(f"파일 분석 중: {file_path}")
    print("=" * 60)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ 오류: JSON 파일이 배열 형식이 아닙니다.")
            return None
        
        # 모델별 개수 세기
        model_counts = Counter()
        for item in data:
            if isinstance(item, dict) and 'model' in item:
                model_counts[item['model']] += 1
        
        return model_counts
        
    except FileNotFoundError:
        print(f"❌ 오류: 파일을 찾을 수 없습니다: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 오류: JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

def main():
    # 분석할 파일 목록
    dump_dir = Path("db_dumps")
    
    # 가장 최신 파일 우선
    files_to_analyze = [
        dump_dir / "db_dump_20251201_103420.json",
        dump_dir / "db_dump_20251107_101020.json",
        dump_dir / "db_dump_20251107_100647.json",
        dump_dir / "db_dump_20251107_100624.json",
    ]
    
    # 존재하는 파일만 필터링
    existing_files = [f for f in files_to_analyze if f.exists()]
    
    if not existing_files:
        print("❌ 분석할 덤프 파일을 찾을 수 없습니다.")
        print(f"   확인 경로: {dump_dir.absolute()}")
        return
    
    # 각 파일 분석
    for file_path in existing_files:
        print(f"\n📁 파일: {file_path.name}")
        print(f"   경로: {file_path}")
        
        model_counts = analyze_db_dump(file_path)
        
        if model_counts:
            print(f"\n📊 테이블별 레코드 개수:")
            print("-" * 60)
            
            # 모델명으로 정렬
            total_records = 0
            for model in sorted(model_counts.keys()):
                count = model_counts[model]
                total_records += count
                # 모델명을 보기 좋게 표시
                model_display = model.replace('myapi.', '').title()
                print(f"  {model_display:30s} : {count:>8,} 개")
            
            print("-" * 60)
            print(f"  {'총 레코드 수':30s} : {total_records:>8,} 개")
            print(f"  {'테이블 수':30s} : {len(model_counts):>8} 개")
            print("=" * 60)
        else:
            print("  ❌ 분석 실패\n")

if __name__ == "__main__":
    main()

