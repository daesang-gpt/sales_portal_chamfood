"""
영업일지의 company_code FK 연결 상태 확인 스크립트
"""
import os
import django

# Django 설정 로드
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
django.setup()

from myapi.models import Report, Company

def check_report_company_fk():
    print("=" * 80)
    print("영업일지의 company_code FK 연결 상태 확인")
    print("=" * 80)
    
    # 전체 영업일지 수
    total_reports = Report.objects.count()
    print(f"\n전체 영업일지 수: {total_reports}")
    
    # company_code FK가 None인 영업일지 찾기
    reports_without_fk = Report.objects.filter(company_code__isnull=True)
    print(f"company_code FK가 없는 영업일지 수: {reports_without_fk.count()}")
    
    # company_name은 있지만 company_code FK가 없는 경우
    reports_with_name_but_no_fk = Report.objects.filter(
        company_code__isnull=True,
        company_name__isnull=False
    ).exclude(company_name='')
    print(f"회사명은 있지만 company_code FK가 없는 영업일지 수: {reports_with_name_but_no_fk.count()}")
    
    # 샘플 출력
    if reports_with_name_but_no_fk.exists():
        print("\n[회사명은 있지만 company_code FK가 없는 영업일지 샘플]")
        for report in reports_with_name_but_no_fk[:10]:
            print(f"ID: {report.id}, 회사명: {report.company_name}, 소재지: {report.company_city_district}")
    
    # company_code FK가 있지만 실제 Company가 존재하지 않는 경우
    reports_with_invalid_fk = []
    reports_with_fk = Report.objects.filter(company_code__isnull=False)
    print(f"\ncompany_code FK가 있는 영업일지 수: {reports_with_fk.count()}")
    
    invalid_count = 0
    for report in reports_with_fk[:100]:  # 샘플로 100개만 체크
        try:
            if report.company_code is None:
                continue
            # company_code FK 접근 시도
            company = report.company_code
            if company is None:
                invalid_count += 1
                reports_with_invalid_fk.append(report)
        except Exception as e:
            invalid_count += 1
            reports_with_invalid_fk.append(report)
    
    if invalid_count > 0:
        print(f"\ncompany_code FK가 있지만 유효하지 않은 영업일지 (샘플 100개 중): {invalid_count}개")
        for report in reports_with_invalid_fk[:5]:
            print(f"ID: {report.id}, company_code FK: {getattr(report, 'company_code_id', None)}")
    
    # company_name으로 Company를 찾을 수 있는지 확인
    print("\n[회사명으로 Company 찾기 시도]")
    fixable_reports = []
    for report in reports_with_name_but_no_fk[:20]:  # 샘플로 20개만 체크
        name = (report.company_name or '').strip()
        city = (report.company_city_district or '').strip()
        
        if not name:
            continue
        
        company = None
        if city:
            companies = Company.objects.filter(company_name=name, city_district=city)
            if companies.count() == 1:
                company = companies.first()
        else:
            companies = Company.objects.filter(company_name=name)
            if companies.count() == 1:
                company = companies.first()
        
        if company:
            fixable_reports.append((report, company))
            print(f"  ID {report.id}: '{name}' -> 찾은 회사: {company.company_code}")
    
    print(f"\n[수정 가능한 영업일지 수]: {len(fixable_reports)}개 (샘플 20개 중)")
    
    return reports_with_name_but_no_fk, fixable_reports

def check_specific_report(report_id):
    """특정 영업일지의 상세 정보 확인"""
    print("=" * 80)
    print(f"영업일지 ID {report_id} 상세 정보")
    print("=" * 80)
    
    try:
        report = Report.objects.get(id=report_id)
        print(f"영업일지 ID: {report.id}")
        print(f"회사명 (company_name): {repr(report.company_name)}")
        print(f"회사코드 (company_code): {repr(report.company_code)}")
        print(f"작성자: {report.author_name}")
        print(f"작성일: {report.createdAt}")
        print(f"방문일: {report.visitDate}")
        print(f"영업단계: {report.sales_stage}")
        
        # company_code 필드의 타입과 값 상세 확인
        print(f"\n=== company_code 상세 분석 ===")
        print(f"company_code 값: {report.company_code}")
        print(f"company_code 타입: {type(report.company_code)}")
        print(f"company_code is None: {report.company_code is None}")
        print(f"company_code == '': {report.company_code == ''}")
        
        if report.company_code:
            print(f"company_code 문자열 길이: {len(str(report.company_code))}")
            print(f"company_code 문자열 표현: '{report.company_code}'")
            
            # FK 관계 확인
            try:
                if hasattr(report.company_code, 'company_name'):
                    company = report.company_code
                    print(f"연결된 회사: {company}")
                    print(f"회사 코드: {company.company_code}")
                    print(f"회사명: {company.company_name}")
                else:
                    print("company_code가 Company 객체가 아닙니다")
            except Exception as fk_error:
                print(f"FK 접근 오류: {fk_error}")
        else:
            print("company_code는 비어있습니다 (None 또는 빈 문자열)")
            
        # 회사명으로 Company 검색해보기
        if report.company_name:
            print(f"\n=== 회사명으로 Company 검색 ===")
            companies = Company.objects.filter(company_name=report.company_name)
            print(f"'{report.company_name}' 이름의 회사 수: {companies.count()}")
            for company in companies:
                print(f"  - {company.company_code}: {company.company_name}")

    except Report.DoesNotExist:
        print(f"영업일지 ID {report_id}를 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

def check_company_existence(company_code):
    """회사 존재 여부 확인"""
    print("=" * 80)
    print(f"회사 코드 {company_code} 존재 여부 확인")
    print("=" * 80)
    
    try:
        company = Company.objects.get(company_code=company_code)
        print(f"✅ 회사 발견!")
        print(f"회사 코드: {company.company_code}")
        print(f"회사명: {company.company_name}")
        print(f"고객분류: {company.customer_classification}")
        print(f"회사유형: {company.company_type}")
        print(f"시/구: {company.city_district}")
        return company
    except Company.DoesNotExist:
        print(f"❌ 회사 코드 {company_code}에 해당하는 회사를 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

if __name__ == '__main__':
    # 올리브푸드 회사 존재 확인
    olive_company = check_company_existence('C0000546')
    
    print("\n" + "=" * 80)
    
    # 영업일지 ID 7462 확인 (올리브푸드 영업일지)
    check_specific_report(7462)
    
    # 비교를 위해 7113도 확인
    print("\n" + "=" * 40 + " 비교용 (쿠즈락) " + "=" * 40)
    check_specific_report(7113)
    
    print("\n" + "=" * 80)
    print("확인 완료")
    print("=" * 80)

