from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Max, Sum, Value
from django.db.models.functions import Replace
from django.utils import timezone
from datetime import timedelta, datetime, date
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from .serializers import CompanySerializer, ReportSerializer, UserSerializer, LoginSerializer, RegisterSerializer, CompanyFinancialStatusSerializer, SalesDataSerializer, ForgotPasswordSerializer, ChangePasswordSerializer
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
import numpy as np
from rest_framework.pagination import PageNumberPagination
from . import models
from rest_framework.generics import ListAPIView
import csv
from django.http import HttpResponse
from django.utils.encoding import escape_uri_path
import pandas as pd
from decimal import Decimal
import logging
import openpyxl
from io import BytesIO
from django.core.mail import send_mail
from django.conf import settings
import secrets
import traceback
import string
from django.db import connection

# 태그 후보 및 임베딩 캐싱
TAG_CANDIDATES = None
TAG_EMBEDDINGS = None
TAG_MODEL = None

# 태그 후보 및 임베딩을 DB에서 불러와 캐싱
def load_tag_candidates_and_embeddings():
    global TAG_CANDIDATES, TAG_EMBEDDINGS, TAG_MODEL
    # 모든 Report의 tags 필드에서 유니크한 태그 추출
    tag_set = set()
    for report in Report.objects.exclude(tags__isnull=True).exclude(tags__exact=''):
        tags = [t.strip() for t in report.tags.split(',') if t.strip()]
        tag_set.update(tags)
    TAG_CANDIDATES = sorted(list(tag_set))
    # 임베딩 모델 준비
    if TAG_MODEL is None:
        TAG_MODEL = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS')
    # 태그 임베딩 생성
    TAG_EMBEDDINGS = TAG_MODEL.encode(TAG_CANDIDATES, convert_to_tensor=True)
    logger = logging.getLogger(__name__)
    logger.debug(f"태그 임베딩 캐싱 완료 - 후보 태그 수: {len(TAG_CANDIDATES)}")

# Create your views here.

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()  # type: ignore[attr-defined]
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Company.objects.all()
        # 검색 파라미터 처리
        search = self.request.query_params.get('search', None)
        customer_classification = self.request.query_params.get('customer_classification', None)
        industry_name = self.request.query_params.get('industry_name', None)
        ordering = self.request.query_params.get('ordering', '-company_code')

        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(employee_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(company_code__icontains=search) |
                Q(company_code_sap__icontains=search)
            )
        if customer_classification:
            queryset = queryset.filter(customer_classification=customer_classification)
        if industry_name:
            queryset = queryset.filter(industry_name__icontains=industry_name)
        return queryset.order_by(ordering)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        company_code = instance.company_code
        
        # 연결된 영업일지(Report)가 있는지 확인
        logger = logging.getLogger(__name__)
        
        try:
            from django.db import connection
            
            # 여러 방식으로 쿼리 시도
            numeric_part = company_code.lstrip('C').lstrip('0') or '0'
            padded_numeric = company_code.lstrip('C')
            
            methods_to_try = [
                ("TO_CHAR 변환 - 전체", "SELECT COUNT(*) FROM REPORTS WHERE TO_CHAR(COMPANY_CODE) = :company_code", {'company_code': company_code}),
                ("TO_CHAR 변환 - 숫자만", "SELECT COUNT(*) FROM REPORTS WHERE TO_CHAR(COMPANY_CODE) = :numeric", {'numeric': numeric_part}),
                ("TO_CHAR 변환 - 패딩숫자", "SELECT COUNT(*) FROM REPORTS WHERE TO_CHAR(COMPANY_CODE) = :padded", {'padded': padded_numeric}),
                ("직접 숫자 비교", "SELECT COUNT(*) FROM REPORTS WHERE COMPANY_CODE = :numeric", {'numeric': int(numeric_part)}),
                ("LPAD 7자리", "SELECT COUNT(*) FROM REPORTS WHERE LPAD(TO_CHAR(COMPANY_CODE), 7, '0') = :padded", {'padded': padded_numeric}),
                ("C + LPAD 조합", "SELECT COUNT(*) FROM REPORTS WHERE 'C' || LPAD(TO_CHAR(COMPANY_CODE), 7, '0') = :company_code", {'company_code': company_code}),
                ("LIKE 패턴", "SELECT COUNT(*) FROM REPORTS WHERE TO_CHAR(COMPANY_CODE) LIKE :pattern", {'pattern': f'%{numeric_part}'}),
            ]
            
            count = 0
            for method_name, sql, params in methods_to_try:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params)
                        count = cursor.fetchone()[0]
                        break
                        
                except Exception as method_error:
                    logger.debug(f"Company 삭제 확인 - {method_name} 실패: {method_error}")
                    continue
            else:
                # 모든 방법이 실패한 경우
                logger.error("모든 쿼리 방법이 실패했습니다")
                raise Exception("모든 쿼리 방법이 실패했습니다")
                
            logger.debug(f"Company 삭제 확인 결과: {count}개의 연관된 Report 발견 (회사코드: {company_code})")
                
            if count > 0:
                return Response(
                    {'error': f'이 회사에 연결된 영업일지가 {count}개 존재하여 삭제할 수 없습니다.'}, 
                    status=status.HTTP_400_BAD_REQUEST, 
                    content_type='application/json'
                )
                    
        except Exception as e:
            logger.error(f"회사 삭제 전 확인 중 오류 발생: {str(e)}", exc_info=True)
            
            # 쿼리 실패 시 안전을 위해 삭제 차단
            return Response(
                {'error': f'회사 삭제 전 확인 중 오류 발생: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content_type='application/json'
            )
        
        # 안전하게 회사 삭제 - Django ORM 대신 우리가 만든 perform_destroy 직접 호출
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"perform_destroy 실패: {e}", exc_info=True)
            return Response(
                {'error': f'회사 삭제 중 오류 발생: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                content_type='application/json'
            )
    
    def perform_destroy(self, instance):
        """Oracle에서 안전한 삭제를 위한 표준 처리"""
        from django.db import transaction, connection
        
        company_code = instance.company_code
        logger = logging.getLogger(__name__)
        
        with transaction.atomic():
            # 각 테이블별로 스키마 정보 확인 후 삭제
            operations = [
                {
                    "name": "CompanyFinancialStatus",
                    "table": "COMPANY_FINANCIAL_STATUS", 
                    "operation": "DELETE",
                    "methods": [
                        ("TO_CHAR 변환", "DELETE FROM COMPANY_FINANCIAL_STATUS WHERE TO_CHAR(COMPANY_CODE) = :company_code", {'company_code': company_code}),
                        ("문자열을 숫자로 변환", "DELETE FROM COMPANY_FINANCIAL_STATUS WHERE COMPANY_CODE = TO_NUMBER(:company_code)", {'company_code': company_code.lstrip('C')}),
                        ("직접 비교", "DELETE FROM COMPANY_FINANCIAL_STATUS WHERE COMPANY_CODE = :company_code", {'company_code': company_code}),
                    ]
                },
                {
                    "name": "Reports",
                    "table": "REPORTS", 
                    "operation": "UPDATE",
                    "methods": [
                        ("TO_CHAR 변환", "UPDATE REPORTS SET COMPANY_CODE = NULL WHERE TO_CHAR(COMPANY_CODE) = :company_code", {'company_code': company_code}),
                        ("문자열을 숫자로 변환", "UPDATE REPORTS SET COMPANY_CODE = NULL WHERE COMPANY_CODE = TO_NUMBER(:company_code)", {'company_code': company_code.lstrip('C')}),
                        ("LPAD 패딩", "UPDATE REPORTS SET COMPANY_CODE = NULL WHERE LPAD(TO_CHAR(COMPANY_CODE), 8, '0') = :company_code", {'company_code': company_code}),
                    ]
                },
                {
                    "name": "Companies",
                    "table": "COMPANIES", 
                    "operation": "DELETE",
                    "methods": [
                        ("직접 비교 (NVARCHAR2)", "DELETE FROM COMPANIES WHERE COMPANY_CODE = :company_code", {'company_code': company_code}),
                        ("Positional", "DELETE FROM COMPANIES WHERE COMPANY_CODE = %s", [company_code]),
                    ]
                }
            ]

            for operation in operations:
                operation_name = operation["name"]
                table_name = operation["table"]
                methods_to_try = operation["methods"]
                
                # 테이블의 COMPANY_CODE 컬럼 정보 확인
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"""
                            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE, NULLABLE 
                            FROM USER_TAB_COLUMNS 
                            WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = 'COMPANY_CODE'
                        """)
                        column_info = cursor.fetchone()
                        if column_info:
                            logger.debug(f"{table_name}.COMPANY_CODE 컬럼 정보: {column_info}")
                        else:
                            logger.debug(f"{table_name}.COMPANY_CODE 컬럼을 찾을 수 없음")
                except Exception as schema_error:
                    logger.debug(f"{table_name} 스키마 정보 확인 실패: {schema_error}")
                
                # 여러 방식으로 쿼리 시도
                success = False
                for method_name, sql, params in methods_to_try:
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql, params)
                            affected_rows = cursor.rowcount
                            logger.debug(f"{operation_name} 처리 완료 ({method_name}): {affected_rows}행 영향받음")
                            success = True
                            break
                            
                    except Exception as method_error:
                        logger.debug(f"{operation_name} 처리 실패 ({method_name}): {method_error}")
                        continue
                
                if not success:
                    error_msg = f"{operation_name} 처리 중 모든 쿼리 방법이 실패했습니다"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
            logger.info(f"Company 삭제 완료: {company_code}")

    def perform_create(self, serializer):
        """회사 생성 시 고객 구분 자동 계산"""
        instance = serializer.save()
        # 고객 구분 자동 계산 및 저장
        instance.customer_classification = instance.calculate_customer_classification()
        instance.save(update_fields=['customer_classification'])
    
    def perform_update(self, serializer):
        """회사 업데이트 시 고객 구분 자동 계산"""
        instance = serializer.save()
        # 고객 구분 자동 계산 및 저장
        instance.customer_classification = instance.calculate_customer_classification()
        instance.save(update_fields=['customer_classification'])

    def create(self, request, *args, **kwargs):
        """회사 생성 시 고객 구분 자동 계산 및 회사코드 자동 생성"""
        # 회사코드가 없으면 자동 생성
        data = dict(request.data)
        if not data.get('company_code') or not data.get('company_code', '').strip():
            # 회사ID 생성: company_code = 'C'+7자리
            last_code = Company.objects.filter(company_code__startswith='C').aggregate(
                max_code=Max('company_code')
            )['max_code']
            if last_code and last_code[1:].isdigit():
                next_num = int(last_code[1:]) + 1
            else:
                next_num = 1
            new_code = f'C{next_num:07d}'
            data['company_code'] = new_code
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """회사 정보 수정 시 재무 정보도 함께 처리하고 고객 구분 자동 계산"""
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        
        # request.data를 dict로 복사 (QueryDict는 수정 불가)
        data = dict(request.data)
        
        # 재무 정보 추출 (별도 처리)
        financial_statuses = data.pop('financial_statuses', None)
        
        # 회사 정보 업데이트
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 재무 정보 처리
        if financial_statuses is not None:
            from django.db import transaction
            from datetime import datetime
            
            with transaction.atomic():
                # 기존 재무 정보 삭제 (제공된 재무 정보만 유지하기 위해)
                # financial_statuses가 빈 배열이면 모든 재무 정보 삭제
                # financial_statuses에 항목이 있으면 해당 항목만 유지하고 나머지 삭제
                
                # 유효한 fiscal_year 목록 수집
                valid_fiscal_years = []
                for financial_data in financial_statuses:
                    if not financial_data.get('fiscal_year'):
                        continue
                    
                    try:
                        fiscal_year_str = financial_data['fiscal_year']
                        if isinstance(fiscal_year_str, str):
                            # YYYY-MM-DD 형식 또는 YYYY 형식 처리
                            if len(fiscal_year_str) == 4:
                                fiscal_year = datetime.strptime(fiscal_year_str + '-01-01', '%Y-%m-%d').date()
                            else:
                                fiscal_year = datetime.strptime(fiscal_year_str.split('T')[0], '%Y-%m-%d').date()
                        else:
                            fiscal_year = fiscal_year_str
                        valid_fiscal_years.append(fiscal_year)
                    except Exception:
                        continue
                
                # 기존 재무 정보 중 유효한 fiscal_year에 해당하지 않는 것들 삭제
                if valid_fiscal_years:
                    # 유효한 fiscal_year에 해당하지 않는 재무 정보 삭제
                    CompanyFinancialStatus.objects.filter(
                        company=instance
                    ).exclude(fiscal_year__in=valid_fiscal_years).delete()
                else:
                    # valid_fiscal_years가 비어있으면 모든 재무 정보 삭제
                    CompanyFinancialStatus.objects.filter(company=instance).delete()
                
                # 재무 정보 생성 또는 업데이트
                for financial_data in financial_statuses:
                    if not financial_data.get('fiscal_year'):
                        continue
                    
                    try:
                        # 날짜 파싱
                        fiscal_year_str = financial_data['fiscal_year']
                        if isinstance(fiscal_year_str, str):
                            # YYYY-MM-DD 형식 또는 YYYY 형식 처리
                            if len(fiscal_year_str) == 4:
                                fiscal_year = datetime.strptime(fiscal_year_str + '-01-01', '%Y-%m-%d').date()
                            else:
                                fiscal_year = datetime.strptime(fiscal_year_str.split('T')[0], '%Y-%m-%d').date()
                        else:
                            fiscal_year = fiscal_year_str
                        
                        # 재무 정보 생성 또는 업데이트
                        CompanyFinancialStatus.objects.update_or_create(
                            company=instance,
                            fiscal_year=fiscal_year,
                            defaults={
                                'total_assets': int(financial_data.get('total_assets', 0) or 0),
                                'capital': int(financial_data.get('capital', 0) or 0),
                                'total_equity': int(financial_data.get('total_equity', 0) or 0),
                                'revenue': int(financial_data.get('revenue', 0) or 0),
                                'operating_income': int(financial_data.get('operating_income', 0) or 0),
                                'net_income': int(financial_data.get('net_income', 0) or 0),
                            }
                        )
                    except Exception as e:
                        # 재무 정보 처리 오류는 무시하거나 로그만 남김
                        logger.debug(f"재무 정보 처리 오류: {e}")
                        pass
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()  # type: ignore[attr-defined]
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 모든 사용자(관리자, 일반 사용자)가 전체 영업일지를 볼 수 있도록 수정
        # Oracle에서 company_code FK는 문자열 타입이므로 select_related 사용 시 문제 발생 가능
        # author만 select_related로 미리 로드 (company_code는 serializer에서 필요 시 로드)
        queryset = Report.objects.select_related('author').all()
        
        # 방문일자 기준으로 내림차순 정렬 (최신순) + 회사명으로 추가 정렬 (일관된 정렬 보장)
        return queryset.order_by('-visitDate', 'company_name')

    def perform_create(self, serializer):
        # 현재 사용자를 author로 설정하고 작성자명, 팀명 저장
        user = self.request.user
        
        # Oracle 호환성을 위해 author는 ID로 명시적으로 전달
        save_kwargs = {
            'author_id': user.id,  # ForeignKey 필드에 ID 직접 전달
            'author_name': user.name if user.name else None,
            'author_department': user.department if user.department else None,
        }
        
        serializer.save(**save_kwargs)
    
    def create(self, request, *args, **kwargs):
        """영업일지 생성 시 회사 데이터 이용 로직"""
        try:
            data = dict(request.data)
            
            # visitDate 날짜 변환 (Oracle 호환성을 위해 명시적으로 변환)
            if 'visitDate' in data:
                visit_date_str = data['visitDate']
                if isinstance(visit_date_str, str):
                    try:
                        # YYYY-MM-DD 형식 파싱
                        data['visitDate'] = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # 다른 날짜 형식 시도
                            data['visitDate'] = datetime.strptime(visit_date_str, '%Y/%m/%d').date()
                        except ValueError:
                            return Response({'error': f'방문일자 형식이 올바르지 않습니다: {visit_date_str}'}, status=status.HTTP_400_BAD_REQUEST)
                elif hasattr(visit_date_str, 'date'):
                    # 이미 date 객체인 경우
                    data['visitDate'] = visit_date_str.date() if hasattr(visit_date_str, 'date') else visit_date_str
            
            # 회사 관련 데이터 추출
            company_location = data.get('location', '')  # 신규 회사 소재지
            company_products = data.get('products', '')
            company_name_input = data.get('company', '')  # 프론트엔드에서 'company' 필드로 회사명 전송
            
            company_obj = None
            
            # 회사 참조가 있는 경우 (Company PK는 company_code 문자열)
            # company_obj는 프론트엔드 호환성을 위해 받지만, 내부적으로는 company_code로 변환
            company_code_value = data.get('company_obj') or data.get('company_code')
            
            # company_name_input이 있으면 우선적으로 처리 (새로운 회사명 입력)
            if company_name_input:
                # 기존 회사명으로 검색
                existing_company = Company.objects.filter(company_name=company_name_input).first()
                if existing_company:
                    company_obj = existing_company
                    # 회사 데이터에서 사용품목을 가져와서 데이터에 설정
                    data['products'] = existing_company.products or company_products
                else:
                    # 신규 회사 생성
                    last_code = Company.objects.filter(company_code__startswith='C').aggregate(
                        max_code=Max('company_code')
                    )['max_code']
                    if last_code and last_code[1:].isdigit():
                        next_num = int(last_code[1:]) + 1
                    else:
                        next_num = 1
                    new_code = f'C{next_num:07d}'
                    
                    # location 정보를 city_district로 설정
                    # 작성자 정보(사원번호, 이름)도 함께 저장
                    new_company = Company.objects.create(
                        company_code=new_code,
                        company_name=company_name_input,
                        customer_classification='잠재',
                        products=company_products,
                        city_district=company_location,  # location을 city_district로 저장
                        employee_number=request.user.employee_number if request.user else None,
                        employee_name=request.user.name if request.user else None
                    )
                    company_obj = new_company
                    data['products'] = company_products
            elif company_code_value:
                # 기존 회사 코드로 검색
                try:
                    company_code = company_code_value
                    # 문자열로 변환 (Oracle 호환성)
                    if not isinstance(company_code, str):
                        company_code = str(company_code)
                    company_obj = Company.objects.get(company_code=company_code)
                    # 회사 데이터에서 사용품목을 가져와서 데이터에 설정
                    data['products'] = company_obj.products or company_products
                except Company.DoesNotExist:
                    return Response({'error': '선택하신 회사를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 회사 정보를 데이터에 추가 (저장용)
            if company_obj:
                data['company_name'] = company_obj.company_name
                data['company_city_district'] = company_obj.city_district  # 원본 값 먼저 설정
                # PrimaryKeyRelatedField에는 primary key 값(company_code)을 전달
                data['company_code_fk'] = company_obj.company_code
            
            # read_only 필드 및 Report 모델에 없는 필드 제거
            data.pop('author', None)
            data.pop('author_name', None)
            data.pop('author_department', None)
            data.pop('team', None)
            data.pop('location', None)  # location은 Report 모델에 없음 (이미 회사의 city_district로 사용됨)
            data.pop('company_obj', None)  # company_obj는 company_code_fk로 변환됨
            data.pop('company', None)  # company(회사명)는 company_name으로 저장됨
            data.pop('company_code', None)  # company_code는 읽기 전용 필드이므로 제거
            
            # 빈 문자열을 None으로 변환 (Oracle 호환성)
            # tags 필드는 null=False이므로 빈 문자열 그대로 유지
            for key in ['sales_stage', 'products', 'company_city_district']:
                if key in data and data[key] == '':
                    data[key] = None
            
            # company_city_district가 None이고 location 정보가 있으면 location 사용
            if data.get('company_city_district') is None and company_location:
                data['company_city_district'] = company_location
                # 기존 회사 정보도 업데이트
                if company_obj and not company_obj.city_district:
                    company_obj.city_district = company_location
                    company_obj.save(update_fields=['city_district'])
            
            # tags는 빈 문자열을 그대로 유지 (null=False이므로)
            if 'tags' in data and data['tags'] == '':
                data['tags'] = ''  # 빈 문자열 유지
            
            # serializer를 직접 생성하여 처리
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            return Response({'error': f'영업일지 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """영업일지 수정 시 회사 데이터 이용 로직"""
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        
        logger = logging.getLogger(__name__)
        logger.debug(f"영업일지 수정 시작 - ID: {instance.id}, company_code: {instance.company_code}")
        
        # 요청 데이터를 dict로 복사
        data = dict(request.data)
        
        # 회사 관련 데이터 추출 및 검증
        company_code_value = data.get('company_obj') or data.get('company_code')
        if company_code_value:
            try:
                company_code = company_code_value
                if not isinstance(company_code, str):
                    company_code = str(company_code)
                company_obj = Company.objects.get(company_code=company_code)
                
                # 회사 정보를 data에 추가
                data['company_name'] = company_obj.company_name
                data['company_city_district'] = company_obj.city_district
                # Company 객체를 company_code 필드에 설정 (FK 업데이트를 위해)
                data['company_code'] = company_obj  # 문자열이 아닌 Company 객체 설정
                # company_obj 필드는 제거 (company_code로 대체)
                data.pop('company_obj', None)
                
                logger.debug(f"Company 객체 설정: {company_obj.company_code} - {company_obj.company_name}")
                
                # 회사 데이터가 있으면 해당 데이터로 설정 (사용자가 입력하지 않았을 때만)
                if not data.get('products') and not instance.products:
                    data['products'] = company_obj.products
            except Company.DoesNotExist:
                # 존재하지 않는 회사 코드인 경우 명확한 에러 메시지 반환
                return Response({
                    'error': f'회사코드 "{company_code}"가 존재하지 않습니다.',
                    'company_code': company_code
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # 기타 예외 처리
                logger.error(f"회사 정보 조회 중 오류: {e}", exc_info=True)
                return Response({
                    'error': f'회사 정보 조회 중 오류가 발생했습니다: {str(e)}',
                    'company_code': company_code_value
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif instance.company_code:
            # instance의 company_code FK를 통해 Company 객체 가져오기
            company_obj = instance.company_code
            # 기존 회사 정보가 있으면 data에 추가
            if not data.get('company_code'):
                data['company_name'] = company_obj.company_name
                data['company_city_district'] = company_obj.city_district
                data['company_code'] = company_obj.company_code
            # company_obj 필드는 제거 (company_code로 대체)
            data.pop('company_obj', None)
        
        # 표준 DRF 방식으로 serializer 생성 및 검증
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        self.perform_update(serializer)
        
        # 최신 데이터 다시 가져오기
        instance.refresh_from_db()
        logger.debug(f"영업일지 수정 완료 - ID: {instance.id}, company_code: {instance.company_code}, company_name: {instance.company_name}")
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)

    def perform_update(self, serializer):
        # 업데이트 시에도 author, author_name, author_department는 변경하지 않음
        # 회사 정보는 serializer의 update 메서드에서 처리되므로 여기서는 추가 처리 불필요
        # 단, validated_data에 company_code가 문자열로 남아있을 경우를 대비한 안전장치
        company_code_value = serializer.validated_data.get('company_code')
        save_kwargs = {}
        
        # company_code는 이미 serializer의 update 메서드에서 처리되었으므로
        # 여기서는 company_name과 company_city_district만 확인
        # (company_code가 validated_data에 남아있고 문자열인 경우에만 처리)
        if company_code_value and isinstance(company_code_value, str):
            try:
                company = Company.objects.get(company_code=company_code_value)
                # 이미 serializer에서 설정되었을 수 있으므로, 없을 때만 설정
                if 'company_name' not in serializer.validated_data:
                    save_kwargs['company_name'] = company.company_name
                if 'company_city_district' not in serializer.validated_data:
                    save_kwargs['company_city_district'] = company.city_district
            except Company.DoesNotExist:
                # 이미 serializer에서 에러 처리가 되었을 것이므로 여기서는 무시
                pass
        
        serializer.save(**save_kwargs)

    def update_with_error_handling(self, request, *args, **kwargs):
        """영업일지 수정 시 더 자세한 오류 처리"""
        logger = logging.getLogger(__name__)
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"영업일지 수정 오류: {e}, 요청 데이터: {request.data}", exc_info=True)
            return Response({
                'error': '영업일지 수정 중 오류가 발생했습니다.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        # GET 또는 OPTIONS 요청 처리 (CORS preflight)
        if request.method == 'GET' or request.method == 'OPTIONS':
            return Response({
                'success': False,
                'message': 'POST 요청만 지원됩니다.'
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # POST 요청 처리
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            id = serializer.validated_data['id']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=id, password=password)
            
            if user is not None:
                refresh = RefreshToken.for_user(user)
                
                # 최초 로그인 여부 확인
                requires_password_change = not getattr(user, 'is_password_changed', False)
                
                return Response({
                    'success': True,
                    'message': '로그인 성공',
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'requires_password_change': requires_password_change,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'department': user.department,
                        'employee_number': user.employee_number,
                        'role': user.role,
                        'is_password_changed': getattr(user, 'is_password_changed', False)
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '아이디 또는 비밀번호가 올바르지 않습니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'success': False,
                'message': '입력 데이터가 올바르지 않습니다.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logging.error(f"Login view error: {str(e)}")
        logging.error(traceback.format_exc())
        return Response({
            'success': False,
            'message': '서버 오류가 발생했습니다.',
            'error': str(e) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    """비밀번호 찾기 - 아이디 입력 시 해당 이메일로 임시 비밀번호 전송"""
    serializer = ForgotPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': '입력 데이터가 올바르지 않습니다.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['id']
    
    try:
        user = User.objects.get(username=username)
        
        # 이메일이 없는 경우
        if not user.email:
            return Response({
                'success': False,
                'message': '등록된 이메일이 없습니다. 관리자에게 문의해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 기존 비밀번호 백업 (롤백용)
        old_password_hash = user.password
        
        # 임시 비밀번호 생성 (영문, 숫자, 특수문자 포함 12자리)
        alphabet = string.ascii_letters + string.digits + string.punctuation
        temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
        
        # 사용자 비밀번호 업데이트
        user.set_password(temp_password)
        user.save()
        
        # 이메일 전송 - 안전하게 콘솔 백엔드 사용
        try:
            # 콘솔 백엔드를 직접 사용하여 SMTP 연결 오류 방지
            from django.core.mail import get_connection
            from django.core.mail.message import EmailMessage
            
            # 이메일 백엔드 확인
            email_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
            
            # SMTP 백엔드인 경우 연결 테스트를 위해 콘솔 백엔드로 대체 (개발 환경)
            if 'smtp' in email_backend.lower() and settings.DEBUG:
                logging.info('개발 환경에서는 콘솔 백엔드를 사용합니다.')
                email_backend = 'django.core.mail.backends.console.EmailBackend'
            
            connection = get_connection(email_backend)
            email = EmailMessage(
                subject='[영업 포털] 임시 비밀번호 발급',
                body=f'''
안녕하세요, {user.name}님.

영업 포털에서 요청하신 임시 비밀번호를 발급해드립니다.

아이디: {user.username}
임시 비밀번호: {temp_password}

보안을 위해 로그인 후 반드시 비밀번호를 변경해주세요.

감사합니다.
                '''.strip(),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                to=[user.email],
                connection=connection,
            )
            email.send()
            
            return Response({
                'success': True,
                'message': f'{user.email}로 임시 비밀번호가 발송되었습니다.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # 이메일 전송 실패 시 비밀번호 롤백
            error_message = str(e)
            error_type = type(e).__name__
            logging.error(f'이메일 전송 실패 [{error_type}]: {error_message}')
            logging.error(f'이메일 전송 상세 오류:', exc_info=True)
            
            try:
                user.password = old_password_hash
                user.save()
                logging.info(f'비밀번호 롤백 완료: {user.username}')
            except Exception as rollback_error:
                logging.error(f'비밀번호 롤백 실패: {str(rollback_error)}')
            
            # 개발 환경에서는 상세 오류 메시지 표시, 운영 환경에서는 일반 메시지
            if settings.DEBUG:
                error_detail = f'{error_type}: {error_message}'
            else:
                error_detail = None
            
            return Response({
                'success': False,
                'message': '이메일 전송 중 오류가 발생했습니다. 비밀번호는 변경되지 않았습니다. 관리자에게 문의해주세요.',
                'error_detail': error_detail if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except User.DoesNotExist:
        # 보안상 존재하지 않는 사용자라고 명확히 알리지 않음
        return Response({
            'success': True,
            'message': '입력하신 아이디로 등록된 이메일이 있다면 임시 비밀번호가 발송됩니다.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logging.error(f'비밀번호 찾기 오류: {str(e)}')
        return Response({
            'success': False,
            'message': '처리 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """비밀번호 변경 API"""
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': '입력 데이터가 올바르지 않습니다.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']
    
    # 현재 비밀번호 확인
    if not user.check_password(current_password):
        return Response({
            'success': False,
            'message': '현재 비밀번호가 올바르지 않습니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 새 비밀번호 설정
    try:
        user.set_password(new_password)
        user.is_password_changed = True
        user.save()
        
        return Response({
            'success': True,
            'message': '비밀번호가 성공적으로 변경되었습니다.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logging.error(f'비밀번호 변경 오류: {str(e)}')
        return Response({
            'success': False,
            'message': '비밀번호 변경 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def company_stats_view(request):
    """회사 통계 정보를 반환하는 API"""
    try:
        # 전체 회사 수
        total_companies = Company.objects.count()
        
        # 잠재 거래처 수 (customer_classification이 '잠재'인 경우)
        potential_customers = Company.objects.filter(
            customer_classification='잠재'
        ).count()
        
        # 신규 거래처 수 (customer_classification이 '신규'인 경우)
        new_customers = Company.objects.filter(
            customer_classification='신규'
        ).count()
        
        # 기존 거래처 수 (customer_classification이 '기존'인 경우)
        existing_customers = Company.objects.filter(
            customer_classification='기존'
        ).count()
        
        return Response({
            'total': total_companies,
            'potentialCustomers': potential_customers,
            'newCustomers': new_customers,
            'existingCustomers': existing_customers
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': '통계 데이터를 가져오는 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """대시보드 통계 정보를 반환하는 API"""
    try:
        print(f"[DEBUG] Dashboard stats API called by user: {request.user.username}")
        import logging
        logger = logging.getLogger(__name__)
        user = request.user
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # 현재 월의 첫날과 마지막날
        from django.utils.dateparse import parse_date
        from calendar import monthrange
        from datetime import timedelta
        
        # 이번 달 범위
        month_first_day = now.replace(day=1)
        month_last_day = now.replace(day=monthrange(current_year, current_month)[1])
        
        # 전월 범위 계산
        try:
            if current_month == 1:
                prev_month_first_day = now.replace(year=current_year-1, month=12, day=1)
                prev_month_last_day = now.replace(year=current_year-1, month=12, day=31)
            else:
                prev_month_first_day = now.replace(month=current_month-1, day=1)
                prev_month_last_day = now.replace(day=monthrange(current_year, current_month-1)[1])
        except Exception as e:
            # 간단한 계산으로 대체
            prev_month_first_day = now.replace(day=1) - timedelta(days=1)
            prev_month_first_day = prev_month_first_day.replace(day=1)
            prev_month_last_day = now.replace(day=1) - timedelta(days=1)
        
        # 사용자별 데이터 필터링
        if hasattr(user, 'role') and user.role == 'admin':
            # 관리자는 전체 데이터
            reports_queryset = Report.objects.all()
            companies_queryset = Company.objects.all()
        else:
            # 일반 사용자는 본인 데이터만
            reports_queryset = Report.objects.filter(author=user)
            # employee_name 필드로 필터링 (username 필드가 제거됨)
            user_name = (user.name or '').strip() if hasattr(user, 'name') else ''
            if user_name:
                companies_queryset = Company.objects.filter(employee_name=user_name)
            else:
                companies_queryset = Company.objects.none()  # 사용자 이름이 없으면 빈 쿼리셋
        
        # 1. 이번 달 영업일지 건수
        this_month_reports = reports_queryset.filter(
            visitDate__year=current_year,
            visitDate__month=current_month
        ).count()
        
        # 전월 영업일지 건수 (증감률 계산용)
        prev_month_reports = reports_queryset.filter(
            visitDate__gte=prev_month_first_day.date(),
            visitDate__lte=prev_month_last_day.date()
        ).count()
        
        reports_growth_rate = 0
        if prev_month_reports > 0:
            reports_growth_rate = round(((this_month_reports - prev_month_reports) / prev_month_reports) * 100)
        
        # 2. 이번 달 신규 고객사 수
        this_month_new_companies = companies_queryset.filter(
            transaction_start_date__year=current_year,
            transaction_start_date__month=current_month
        ).count()
        
        # 3. 총 영업 활동 (대면/전화 분리)
        total_face_to_face = reports_queryset.filter(type='대면').count()
        total_phone = reports_queryset.filter(type='전화').count()
        total_contacts = total_face_to_face + total_phone
        
        # 4. 이번 달 매출 (실제 SalesData 기반)
        this_month_revenue = 0
        try:
            # 이번 달 SalesData 조회
            this_month_sales = SalesData.objects.filter(
                매출일자__year=current_year,
                매출일자__month=current_month
            )
            
            # 사용자별 필터링 (이름 공백 제거 매칭 포함)
            normalized_name = (user.name or '').replace(' ', '') if hasattr(user, 'name') else ''
            this_month_sales = this_month_sales.annotate(
                매출담당자_norm=Replace('매출담당자', Value(' '), Value('')),
                담당자_norm=Replace('담당자', Value(' '), Value(''))
            )
            if not (hasattr(user, 'role') and user.role == 'admin'):
                this_month_sales = this_month_sales.filter(
                    Q(매출담당자_norm__icontains=normalized_name)
                )
            
            # 이번 달 매출 합계
            this_month_revenue = sum(sales.매출금액 for sales in this_month_sales)
            
            # 매출이 0이면 영업일지 기반 추정
            if this_month_revenue == 0:
                this_month_revenue = this_month_reports * 30000000  # 영업일지 1건당 약 3천만원 가정
                
        except Exception as e:
            # 매출 데이터가 없거나 오류 발생 시 기본값
            this_month_revenue = this_month_reports * 30000000  # 영업일지 1건당 약 3천만원 가정
        
        # 전월 매출 (비슷한 방식으로 계산, 실제로는 별도 로직 필요)
        revenue_growth_rate = 15.5  # 임시로 고정값 사용
        
        return Response({
            'thisMonthReports': this_month_reports,
            'reportsGrowthRate': reports_growth_rate,
            'thisMonthNewCompanies': this_month_new_companies,
            'totalContacts': total_contacts,
            'faceToFaceContacts': total_face_to_face,
            'phoneContacts': total_phone,
            'thisMonthRevenue': this_month_revenue,
            'revenueGrowthRate': revenue_growth_rate
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Dashboard stats API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': '대시보드 통계 데이터를 가져오는 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_charts_data_view(request):
    """대시보드 차트 데이터를 반환하는 API"""
    try:
        print(f"[DEBUG] Dashboard charts API called by user: {request.user.username}")
        user = request.user
        
        # 사용자별 데이터 필터링
        if hasattr(user, 'role') and user.role == 'admin':
            reports_queryset = Report.objects.all()
            companies_queryset = Company.objects.all()
        else:
            reports_queryset = Report.objects.filter(author=user)
            # employee_name 필드로 필터링 (username 필드가 제거됨)
            user_name = (user.name or '').strip() if hasattr(user, 'name') else ''
            if user_name:
                companies_queryset = Company.objects.filter(employee_name=user_name)
            else:
                companies_queryset = Company.objects.none()  # 사용자 이름이 없으면 빈 쿼리셋
        
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # 최근 6개월 매출 추이 데이터 생성 (실제 SalesData 기반)
        from datetime import datetime, timedelta
        from calendar import monthrange
        sales_data = []
        
        for i in range(6):  # 최근 6개월 (0 = 현재월, 5 = 5개월 전)
            # 정확한 월 계산
            target_year = current_year
            target_month = current_month - i
            
            if target_month <= 0:
                target_month += 12
                target_year -= 1
            
            month_name = f"{target_month}월"
            
            # 해당 월의 실제 매출 데이터 조회
            monthly_sales_queryset = SalesData.objects.filter(
                매출일자__year=target_year,
                매출일자__month=target_month
            )
            
            # 사용자별 필터링 (관리자가 아닌 경우) - 이름 공백 제거 매칭 포함
            normalized_name = (user.name or '').replace(' ', '') if hasattr(user, 'name') else ''
            monthly_sales_queryset = monthly_sales_queryset.annotate(
                매출담당자_norm=Replace('매출담당자', Value(' '), Value('')),
                담당자_norm=Replace('담당자', Value(' '), Value(''))
            )
            if not (hasattr(user, 'role') and user.role == 'admin'):
                monthly_sales_queryset = monthly_sales_queryset.filter(
                    Q(매출담당자_norm__icontains=normalized_name)
                )
            
            # 월별 매출 합계 계산
            monthly_revenue = sum((sales.매출금액 or 0) for sales in monthly_sales_queryset)
            monthly_profit = sum((sales.매출이익 or 0) for sales in monthly_sales_queryset)
            monthly_quantity = sum((sales.Box or 0) for sales in monthly_sales_queryset)
            monthly_transactions = monthly_sales_queryset.count()
      
            sales_data.append({
                'name': month_name,
                '매출액': monthly_revenue,
                '매출이익': monthly_profit,
                '매출수량': monthly_quantity or (monthly_transactions * 50),  # 월련량 또는 추정량
                '매출건수': monthly_transactions
            })
        
        # 시간순으로 정렬 (최근 6개월 전부터 현재까지)
        sales_data = list(reversed(sales_data))
        
        # 채널별 매출 비율 데이터 생성: 최근 6개월 SalesData의 '유통형태' 기준 매출금액 비중
        from calendar import monthrange
        try:
            # 최근 6개월 기간 계산
            latest_year, latest_month = current_year, current_month
            earliest_dt = now
            for i in range(5, -1, -1):
                ty, tm = current_year, current_month - i
                if tm <= 0:
                    tm += 12
                    ty -= 1
                # 첫 월의 1일
                if i == 5:
                    earliest_dt = earliest_dt.replace(year=ty, month=tm, day=1)
            start_date = earliest_dt.date()
            end_date = now.replace(day=monthrange(current_year, current_month)[1]).date()

            channel_qs = SalesData.objects.filter(매출일자__gte=start_date, 매출일자__lte=end_date)
            if not (hasattr(user, 'role') and user.role == 'admin'):
                # 일반 사용자는 매출담당자 기준으로 필터링
                channel_qs = channel_qs.annotate(
                    매출담당자_norm=Replace('매출담당자', Value(' '), Value(''))
                ).filter(
                    Q(매출담당자_norm__icontains=normalized_name)
                )
            grouped = channel_qs.values('유통형태').annotate(
                total=Sum('매출금액'),
                profit=Sum('매출이익'),
            ).order_by('-total')
            total_sum = sum((row['total'] or 0) for row in grouped)
            colors = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#AF19FF", "#00B8D9"]
            channel_data = []
            if total_sum > 0 and grouped:
                for idx, row in enumerate(grouped):
                    name = row['유통형태'] or '미지정'
                    percent = round((row['total'] or 0) * 100 / total_sum)
                    channel_data.append({
                        'name': name,
                        'value': percent,
                        'color': colors[idx % len(colors)],
                        'revenue': int(row['total'] or 0),
                        'profit': int(row['profit'] or 0),
                    })
            else:
                channel_data = [
                    {'name': '미지정', 'value': 100, 'color': '#0088FE'}
                ]
        except Exception as e:
            # 오류 발생 시 기본값 설정
            channel_data = [
                {'name': '미지정', 'value': 100, 'color': '#0088FE'}
            ]
        
        # 최근 영업 활동 데이터
        recent_activities = []
        try:
            recent_reports = reports_queryset.order_by('-visitDate')[:4]
            
            for report in recent_reports:
                recent_activities.append({
                    'company': report.company_name or '알 수 없음',
                    'type': report.type,
                    'date': report.visitDate.strftime('%Y-%m-%d'),
                    'author': report.author.name if report.author else 'Unknown'
                })
        except Exception as e:
            # 오류 발생 시 기본값 설정
            recent_activities = [
                {'company': '데이터 없음', 'type': '대면', 'date': '2025-01-01', 'author': '시스템'}
            ]
        
        return Response({
            'salesData': sales_data,
            'channelData': channel_data,
            'recentActivities': recent_activities
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"[ERROR] Dashboard charts API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': '차트 데이터를 가져오는 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        if user is not None:
            return Response({
                'success': True,
                'message': '회원가입 성공',
                'user': {
                    'id': getattr(user, 'id', None),
                    'username': getattr(user, 'username', None),
                    'name': getattr(user, 'name', None),
                    'department': getattr(user, 'department', None),
                    'employee_number': getattr(user, 'employee_number', None),
                    'role': getattr(user, 'role', None)
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': '회원가입 처리 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'success': False,
            'message': '입력 데이터가 올바르지 않습니다.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_suggest_view(request):
    """회사명 자동완성을 위한 API - 회사명 (시/구) 형식으로 반환"""
    try:
        query = request.GET.get('query', '').strip()
        
        if not query or len(query) < 1:
            return Response([], status=status.HTTP_200_OK)
        
        # 회사명으로 LIKE 검색 (대소문자 구분 없음)
        companies = Company.objects.filter(
            company_name__icontains=query
        )[:10]  # 최대 10개
        
        # 응답 형식: [{"id": "C0000001", "name": "회사명 (시/구)"}, ...]
        suggestions = []
        for company in companies:
            display_info = []
            
            # 시/구 정보만 표시
            if company.city_district:
                display_info.append(company.city_district)
            
            # 표시 문자열 생성
            display_name = company.company_name
            if display_info:
                display_name += f' ({", ".join(display_info)})'
            
            suggestions.append({
                "id": company.company_code,
                "name": display_name
            })
        
        return Response(suggestions, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': '회사 검색 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_create_company(request):
    """
    회사명으로 신규 회사 자동 등록 API
    - 회사명이 DB에 없으면 'C'+7자리 순차 ID, 고객분류 '신규'로 생성
    - 이미 있으면 중복 등록하지 않고 기존 회사 반환
    - 작성자 정보(사원번호, 이름)와 소재지 정보도 함께 저장
    """
    name = request.data.get('company_name')
    if not name:
        return Response({'error': '회사명이 필요합니다.'}, status=400)
    # 중복 체크 (회사명 완전일치)
    company = Company.objects.filter(company_name=name).first()
    if company:
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=200)
    # 회사ID 생성: company_code = 'C'+7자리
    last_code = Company.objects.filter(company_code__startswith='C').aggregate(
        max_code=Max('company_code')
    )['max_code']
    if last_code and last_code[1:].isdigit():
        next_num = int(last_code[1:]) + 1
    else:
        next_num = 1
    new_code = f'C{next_num:07d}'
    
    # 사용자 정보 및 소재지 정보 추출
    location = request.data.get('location', '')
    employee_number = request.user.employee_number if request.user else None
    employee_name = request.user.name if request.user else None
    
    company = Company.objects.create(
        company_code=new_code,
        company_name=name,
        customer_classification='잠재',
        city_district=location if location else None,
        employee_number=employee_number,
        employee_name=employee_name
    )
    serializer = CompanySerializer(company)
    return Response(serializer.data, status=201)

# API: content에서 추출된 키워드를 DB 태그와 유사도 매칭하여 반환
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_keywords_view(request):
    """
    영업일지 텍스트에서 키워드를 추출하고, DB에 저장된 최신 태그값과 유사도가 가장 높은 태그로 매핑하여 반환합니다.
    - DB 태그 중 입력 텍스트에 실제로 등장하는 태그는 무조건 포함
    - 나머지는 KeyBERT 후보와 DB 태그 임베딩 유사도 기반으로 보완
    - 태그/임베딩은 최초 1회만 캐싱, 속도 개선
    """
    try:
        print("[키워드 추출 API] 요청 수신됨")
        text = request.data.get('text', '').strip()
        print(f"[키워드 추출 API] 입력 텍스트 길이: {len(text)}")
        if not text:
            return Response({'error': '텍스트가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        # 태그 후보 및 임베딩 캐싱 (최초 1회만)
        global TAG_CANDIDATES, TAG_EMBEDDINGS, TAG_MODEL
        if TAG_CANDIDATES is None or TAG_EMBEDDINGS is None or TAG_MODEL is None:
            print("[키워드 추출 API] 태그 캐싱 시작")
            load_tag_candidates_and_embeddings()
            print("[키워드 추출 API] 태그 캐싱 완료")
        # 1. 입력 문장에 실제로 등장하는 DB 태그 우선 추출
        direct_tags = [tag for tag in TAG_CANDIDATES if tag and tag in text]
        print(f"[키워드 추출 API] 직접 매칭된 태그: {direct_tags}")
        print(f"[키워드 추출 API] DB 태그 후보 수: {len(TAG_CANDIDATES)}")
        
        # 2. KeyBERT로 후보 추출
        print("[키워드 추출 API] KeyBERT 추출 시작")
        kw_model = KeyBERT(model=TAG_MODEL)
        keybert_keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words=None,
            top_n=10  # 기존 20 → 10으로 속도 개선
        )
        candidates = [kw[0] if not isinstance(kw[0], tuple) else ' '.join(kw[0]) for kw in keybert_keywords]
        print(f"[키워드 추출 API] KeyBERT 후보: {candidates}")
        
        # 항상 KeyBERT 결과를 포함하고, DB 태그가 있을 때만 유사도 매칭 추가
        result_tags = set(direct_tags)
        
        # DB 태그가 있고 많이 매칭되었다면 유사도 매칭 시도
        if len(TAG_CANDIDATES) > 0 and len(candidates) > 0:
            candidate_embeddings = TAG_MODEL.encode(candidates, convert_to_tensor=True)
            for i, cand_emb in enumerate(candidate_embeddings):
                cos_scores = util.pytorch_cos_sim(cand_emb, TAG_EMBEDDINGS)[0]
                best_idx = int(np.argmax(cos_scores))
                best_score = float(cos_scores[best_idx])
                candidate = candidates[i]
                db_tag = TAG_CANDIDATES[best_idx]
                
                # 유사도가 높거나 텍스트에 직접 포함되면 추가
                if db_tag in text:
                    result_tags.add(db_tag)
                elif best_score >= 0.75:  
                    result_tags.add(db_tag)
                    print(f"[키워드 추출 API] 유사도 매칭: {candidate} -> {db_tag} (점수: {best_score:.2f})")
        
        # KeyBERT 결과도 직접 추가 (중복 제거)
        for candidate in candidates:
            if candidate and len(candidate.strip()) > 0:
                result_tags.add(candidate.strip())
        
        # 최종 결과 정리
        result_tags = [tag for tag in result_tags if tag and len(tag.strip()) > 0][:10]
        
        print(f"[키워드 추출 API] 최종 결과: {result_tags}")
        # 최대 10개 반환
        return Response({
            'keywords': result_tags
        }, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[키워드 추출 API] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': '키워드 추출 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SalesReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return Response({
            'results': data,
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number
        })

class SalesReportListView(ListAPIView):
    serializer_class = ReportSerializer
    pagination_class = SalesReportPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            # 모든 사용자(관리자, 일반 사용자)가 전체 영업일지를 볼 수 있도록 수정
            # Oracle에서 company_code FK는 문자열 타입이므로 select_related 사용 시 문제 발생 가능
            # author만 select_related로 미리 로드 (company_code는 serializer에서 필요 시 로드)
            # 데이터베이스 연결 문제를 방지하기 위해 select_related를 안전하게 사용
            # select_related는 쿼리 최적화를 위한 것이므로 실패해도 일반 쿼리셋으로 폴백 가능
            queryset = Report.objects.all()
            try:
                # select_related를 시도하되, 실패해도 계속 진행
                queryset = queryset.select_related('author')
            except Exception as e:
                # select_related 실패 시 일반 쿼리셋 사용 (N+1 쿼리 문제는 있지만 동작은 함)
                print(f"[SalesReportListView] select_related 실패, 일반 쿼리셋 사용: {str(e)}")
                queryset = Report.objects.all()
            
            # 검색/필터/정렬
            search = self.request.query_params.get('search', '').strip()
            period = self.request.query_params.get('period', 'all')
            ordering = self.request.query_params.get('ordering', '-visitDate')
            company_id = self.request.query_params.get('companyId', '').strip()
            
            # 동일한 방문일자일 때 일관된 정렬을 위해 회사명을 추가 정렬 기준으로 사용
            # ordering이 방문일자만 포함하는 경우 회사명을 추가
            if ordering and ordering.strip():
                ordering_parts = [o.strip() for o in ordering.split(',')]
                # 방문일자 관련 정렬만 있고 회사명 정렬이 없는 경우 추가
                has_visit_date = any('visitDate' in part or 'visit_date' in part for part in ordering_parts)
                has_company_name = any('company_name' in part for part in ordering_parts)
                if has_visit_date and not has_company_name:
                    # 방문일자 정렬에 회사명을 추가 정렬 기준으로 추가
                    ordering = f"{ordering},company_name"
            else:
                # 기본 정렬: 방문일자 내림차순 + 회사명 오름차순
                ordering = '-visitDate,company_name'

            if company_id:
                # company_code FK는 to_field='company_code'로 설정되어 있으므로 직접 비교 가능
                # company_obj FK도 함께 체크
                # Company 객체를 먼저 찾아서 사용하면 더 정확함
                try:
                    company = Company.objects.get(company_code=company_id)
                    # Company 객체가 있으면 이를 사용하여 필터링
                    # 동일한 company_code를 가진 영업일지만 필터링 (company_name 제외)
                    queryset = queryset.filter(company_code=company)
                    print(f"[SalesReportListView] companyId 필터링 (Company 객체 사용, company_code만): {company_id}")
                except Company.DoesNotExist:
                    # Company가 없으면 문자열 company_code로만 필터링 (company_name 제외)
                    queryset = queryset.filter(company_code=company_id)
                    print(f"[SalesReportListView] companyId 필터링 (문자열, company_code만): {company_id}")
                except Exception as e:
                    # 기타 예외 발생 시 로깅하고 안전한 필터링으로 폴백
                    print(f"[SalesReportListView] companyId 필터링 중 예외 발생: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 안전한 필터링으로 폴백 (company_code만)
                    queryset = queryset.filter(company_code=company_id)
            if search:
                # 검색 필터 구성 - author_name은 저장된 필드이므로 안전하게 사용
                # author FK 관련 필터는 select_related로 로드되었지만, 안전성을 위해 분리
                search_filters = (
                    Q(company_name__icontains=search) |
                    Q(author_name__icontains=search) |
                    Q(tags__icontains=search)
                )
                
                # author FK 관련 필터 추가 (author는 CASCADE이므로 항상 존재해야 함)
                # 하지만 데이터베이스 연결 문제나 쿼리 최적화 문제를 방지하기 위해 안전하게 처리
                author_filters = Q(author__username__icontains=search) | Q(author__name__icontains=search)
                search_filters |= author_filters
                
                # 쿼리 실행 시 예외 처리
                try:
                    queryset = queryset.filter(search_filters)
                except Exception as e:
                    # 쿼리 실행 실패 시 author 필터 없이 재시도
                    print(f"[SalesReportListView] 검색 필터 실행 중 오류 발생, author 필터 제외하고 재시도: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # author 필터 없이 재시도
                    search_filters_fallback = (
                        Q(company_name__icontains=search) |
                        Q(author_name__icontains=search) |
                        Q(tags__icontains=search)
                    )
                    queryset = queryset.filter(search_filters_fallback)
            if period in ['1m', '3m', '6m']:
                months = int(period[0])
                start_date = timezone.now().date() - timedelta(days=30 * months)
                queryset = queryset.filter(visitDate__gte=start_date)
            
            # 정렬 처리 - 예외 발생 시 기본 정렬 사용
            try:
                # ordering이 문자열인 경우 쉼표로 분리하여 처리
                if isinstance(ordering, str):
                    ordering_list = [o.strip() for o in ordering.split(',') if o.strip()]
                    queryset = queryset.order_by(*ordering_list)
                else:
                    queryset = queryset.order_by(ordering)
            except Exception as e:
                print(f"[SalesReportListView] order_by 실패, 기본 정렬 사용: {str(e)}")
                # 기본 정렬로 폴백: 방문일자 내림차순 + 회사명 오름차순
                try:
                    queryset = queryset.order_by('-visitDate', 'company_name')
                except Exception as e2:
                    print(f"[SalesReportListView] 기본 정렬도 실패: {str(e2)}")
                    # 최후의 수단: 방문일자만
                    queryset = queryset.order_by('-visitDate')
            
            return queryset
        except Exception as e:
            import traceback
            print(f"[SalesReportListView get_queryset] 오류 발생: {str(e)}")
            traceback.print_exc()
            # 빈 쿼리셋 반환
            return Report.objects.none()
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            import traceback
            print(f"[SalesReportListView list] 오류 발생: {str(e)}")
            traceback.print_exc()
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {'error': f'영업일지 목록을 불러오는 중 오류가 발생했습니다: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CompanyFinancialStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.CompanyFinancialStatus.objects.all()
    serializer_class = CompanyFinancialStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 회사 코드로 필터링 (company_code 또는 company_code_sap)
        company_code = self.request.query_params.get('company__company_code', None)
        company_code_sap = self.request.query_params.get('company__company_code_sap', None)
        
        # 필터링 조건이 없으면 모든 데이터 반환
        if not company_code and not company_code_sap:
            return models.CompanyFinancialStatus.objects.all()
        
        queryset = models.CompanyFinancialStatus.objects.all()
        
        # company_code로 필터링
        if company_code:
            queryset = queryset.filter(company__company_code=company_code)
        
        # company_code_sap로 필터링
        if company_code_sap:
            queryset = queryset.filter(company__company_code_sap=company_code_sap)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"CompanyFinancialStatus 조회 중 오류: {e}", exc_info=True)
            from rest_framework.response import Response
            from rest_framework import status
            return Response(
                {'error': str(e), 'detail': '재무정보 조회 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SalesDataViewSet(viewsets.ModelViewSet):
    queryset = SalesData.objects.all()
    serializer_class = SalesDataSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'admin':
            # 관리자는 전체 데이터 접근 가능
            queryset = SalesData.objects.all()
        else:
            # 일반 사용자는 본인 관련 데이터만 접근 가능
            normalized_name = (user.name or '').replace(' ', '') if hasattr(user, 'name') else ''
            queryset = SalesData.objects.all().annotate(
                매출담당자_norm=Replace('매출담당자', Value(' '), Value(''))
            ).filter(
                Q(매출담당자_norm__icontains=normalized_name) |
                Q(company_obj__employee_name__icontains=normalized_name)  # SalesData 모델의 company_obj는 유지됨
            )
        
        # 날짜 필터링
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(매출일자__gte=start_date)
        if end_date:
            queryset = queryset.filter(매출일자__lte=end_date)
            
        return queryset.order_by('-매출일자')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_reports_csv(request):
    """영업일지 데이터를 CSV로 다운로드"""
    try:
        # 관리자 권한 확인
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': '관리자만 다운로드할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 모든 영업일지 데이터 조회
        # Oracle 타입 변환 오류를 방지하기 위해 필요한 필드만 가져오기
        reports = Report.objects.only(
            'id', 'author_department', 'visitDate', 'company_name', 'company_code', 'type', 
            'products', 'content', 'tags', 'createdAt', 'author_id'
        ).select_related('author', 'company_code').iterator(chunk_size=100)
        
        # CSV 응답 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path("영업일지_백업.csv")}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        writer = csv.writer(response)
        
        # 헤더 작성
        writer.writerow([
            'ID', '작성자ID', '작성자명', '팀명', '방문일자', '회사명', '회사코드', '영업형태',
            '사용품목', '미팅내용', '태그', '작성일'
        ])
        
        # 안전하게 문자열로 변환하는 헬퍼 함수 (Oracle 타입 변환 오류 방지)
        def safe_str(value, default=''):
            """값을 안전하게 문자열로 변환"""
            if value is None:
                return default
            try:
                # 숫자도 문자열로 변환
                if isinstance(value, (int, float)):
                    return str(int(value))
                # Decimal 등도 처리
                if hasattr(value, '__str__'):
                    return str(value).strip()
                return default
            except:
                try:
                    return str(value)
                except:
                    return default
        
        # 데이터 작성
        row_count = 0
        for report in reports:
            try:
                # 객체에서 직접 값 가져오기 (모두 문자열로 안전하게 변환)
                report_id = safe_str(report.id, '')
                
                # author 처리
                author_id = ''
                author_name = ''
                try:
                    # author_id는 ForeignKey의 실제 값
                    if hasattr(report, 'author_id'):
                        author_id_val = report.author_id
                        if author_id_val is not None:
                            author_id = safe_str(author_id_val, '')
                    # author 객체가 로드된 경우
                    if hasattr(report, 'author') and report.author:
                        if not author_id and hasattr(report.author, 'id'):
                            author_id = safe_str(report.author.id, '')
                        if hasattr(report.author, 'name'):
                            author_name = safe_str(report.author.name, '')
                except Exception as e:
                    logging.warning(f'Report ID {report_id}: author 접근 오류 - {e}')
                
                # 기본 필드들 (직접 접근하여 값 가져오기)
                team = safe_str(report.author_department, '')
                company_name = safe_str(report.company_name, '')
                report_type = safe_str(report.type, '')
                products = safe_str(report.products, '')
                content = safe_str(report.content, '')
                tags = safe_str(report.tags, '')
                
                # company_code FK 처리 (Company의 PK가 company_code(문자열))
                company_code = ''
                try:
                    # company_code FK를 통해 접근
                    if report.company_code:
                        company_code = safe_str(report.company_code.company_code, '')
                except Exception as e:
                    logging.warning(f'Report ID {report_id}: company_code 접근 오류 - {e}')
                
                # 날짜 필드 처리 (문자열로 변환)
                visit_date = ''
                try:
                    if hasattr(report, 'visitDate') and report.visitDate:
                        visit_date_obj = report.visitDate
                        if isinstance(visit_date_obj, str):
                            visit_date = visit_date_obj[:10] if len(visit_date_obj) >= 10 else visit_date_obj
                        elif hasattr(visit_date_obj, 'strftime'):
                            visit_date = visit_date_obj.strftime('%Y-%m-%d')
                        else:
                            visit_date = safe_str(visit_date_obj, '')
                except Exception as e:
                    logging.warning(f'Report ID {report_id}: visitDate 처리 오류 - {e}')
                
                # 작성일 처리
                created_at = ''
                try:
                    if hasattr(report, 'createdAt') and report.createdAt:
                        created_at_obj = report.createdAt
                        if isinstance(created_at_obj, str):
                            created_at = created_at_obj[:19] if len(created_at_obj) >= 19 else created_at_obj
                        elif hasattr(created_at_obj, 'strftime'):
                            created_at = created_at_obj.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            created_at = safe_str(created_at_obj, '')
                except Exception as e:
                    logging.warning(f'Report ID {report_id}: createdAt 처리 오류 - {e}')
                
                # 디버깅: 첫 번째 행만 로깅
                if row_count == 0:
                    logging.info(f'첫 번째 행 샘플 - ID: {report_id}, 회사명: {company_name}, 내용: {content[:50] if content else "없음"}')
                
                # CSV writer에 모든 값을 문자열로 전달
                writer.writerow([
                    report_id,
                    author_id,
                    author_name,
                    team,
                    visit_date,
                    company_name,
                    company_code,
                    report_type,
                    products,
                    content,
                    tags,
                    created_at
                ])
                row_count += 1
                
            except Exception as row_error:
                # 개별 행 처리 오류는 로깅만 하고 계속 진행
                import traceback
                error_trace = traceback.format_exc()
                try:
                    if isinstance(report, dict):
                        report_id_for_error = safe_str(report.get('id', ''), 'unknown')
                    else:
                        report_id_for_error = safe_str(getattr(report, 'id', ''), 'unknown')
                except:
                    report_id_for_error = 'unknown'
                logging.error(f'영업일지 CSV 다운로드 중 행 처리 오류 (ID: {report_id_for_error}): {row_error}\n{error_trace}')
                continue
        
        logging.info(f'영업일지 CSV 다운로드 완료: {row_count}개 행 처리됨')
        
        return response
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f'영업일지 CSV 다운로드 오류: {e}\n{error_trace}')
        return Response({
            'error': f'다운로드 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_companies_csv(request):
    """회사 데이터를 CSV로 다운로드"""
    try:
        # 관리자 권한 확인
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': '관리자만 다운로드할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 모든 회사 데이터 조회
        companies = Company.objects.all()
        
        # CSV 응답 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path("회사_백업.csv")}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        writer = csv.writer(response)
        
        # 헤더 작성 (기본정보)
        writer.writerow([
            '회사코드', '회사명', '고객분류', '회사유형', '사업자등록번호', '설립일', '대표자명',
            '본사 주소', '시/구', '공장 주소', '대표전화', '업종명', '주요제품', '웹사이트', '참고사항',
            # SAP정보
            'SAP코드여부', 'SAP거래처코드', '사업', '사업부', '지점/팀', '팀명', '사원번호', '영업 사원',
            '유통형태코드', '유통형태', '거래처 담당자', '담당자 연락처', '코드생성일', '거래시작일', '결제조건'
        ])
        
        # 데이터 작성
        for company in companies:
            writer.writerow([
                # 기본정보
                company.company_code or '',
                company.company_name or '',
                company.customer_classification or '',
                company.company_type or '',
                company.tax_id or '',
                company.established_date.strftime('%Y-%m-%d') if company.established_date else '',
                company.ceo_name or '',
                company.head_address or '',
                company.city_district or '',
                company.processing_address or '',
                company.main_phone or '',
                company.industry_name or '',
                company.products or '',
                company.website or '',
                company.remarks or '',
                # SAP정보
                company.sap_code_type or '',
                company.company_code_sap or '',
                company.biz_code or '',
                company.biz_name or '',
                company.department_code or '',
                company.department or '',
                company.employee_number or '',
                company.employee_name or '',
                company.distribution_type_sap_code or '',
                company.distribution_type_sap or '',
                company.contact_person or '',
                company.contact_phone or '',
                company.code_create_date.strftime('%Y-%m-%d') if company.code_create_date else '',
                company.transaction_start_date.strftime('%Y-%m-%d') if company.transaction_start_date else '',
                company.payment_terms or '',
            ])
        
        return response
        
    except Exception as e:
        logging.error(f'회사 CSV 다운로드 오류: {e}')
        return Response({'error': '다운로드 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_reports_csv(request):
    """영업일지 CSV/TSV 파일을 업로드하여 일괄 업데이트/생성"""
    try:
        # 관리자 권한 확인
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': '관리자만 업로드할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        if 'file' not in request.FILES:
            return Response({'error': '파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 기존 데이터 삭제 여부 확인
        delete_existing = request.data.get('delete_existing', 'false').lower() == 'true'
        
        csv_file = request.FILES['file']
        
        # 파일 확장자 확인 및 읽기
        file_extension = csv_file.name.lower().split('.')[-1]
        if file_extension not in ['csv', 'xlsx', 'tsv']:
            return Response({'error': 'CSV, TSV 또는 XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file_extension == 'tsv':
                # TSV 파일 읽기
                csv_file.seek(0)  # 파일 포인터를 처음으로
                df = pd.read_csv(csv_file, sep='\t', encoding='utf-8')
            elif file_extension == 'csv':
                df = pd.read_csv(csv_file, encoding='utf-8')
            else:  # xlsx
                df = pd.read_excel(BytesIO(csv_file.read()))
        except Exception as e:
            return Response({'error': f'파일 읽기 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 기존 영업일지 삭제
        if delete_existing:
            deleted_count = Report.objects.all().delete()[0]
            logging.info(f'기존 영업일지 {deleted_count}개 삭제됨')
        else:
            deleted_count = 0
        
        # 필요한 컬럼 확인
        required_columns = ['작성자ID', '작성자명', '팀명', '방문일자', '회사ID', '회사명', '영업형태', '미팅 내용']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return Response({'error': f'파일에 필요한 컬럼이 없습니다: {", ".join(missing_columns)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 작성자ID (employee_number로 조회)
                author = None
                author_id_str = str(row['작성자ID']).strip() if pd.notna(row['작성자ID']) else ''
                if author_id_str:
                    try:
                        author = User.objects.get(employee_number=author_id_str)
                    except User.DoesNotExist:
                        errors.append(f"행 {index + 2}: 작성자를 찾을 수 없습니다 (작성자ID: {author_id_str})")
                        continue
                    except User.MultipleObjectsReturned:
                        author = User.objects.filter(employee_number=author_id_str).first()
                
                if not author:
                    errors.append(f"행 {index + 2}: 작성자 정보가 없습니다")
                    continue
                
                # 작성자 정보 저장 (TSV에서 직접 가져오거나 User에서)
                author_name = row['작성자명'] if pd.notna(row.get('작성자명')) else (author.name if author else '')
                author_department = row['팀명'] if pd.notna(row.get('팀명')) else (author.department if author else '')
                
                # 회사ID (company_code로 조회)
                company_obj = None
                company_id_str = str(row['회사ID']).strip() if pd.notna(row['회사ID']) else ''
                if company_id_str:
                    try:
                        company_obj = Company.objects.get(company_code=company_id_str)
                    except Company.DoesNotExist:
                        errors.append(f"행 {index + 2}: 회사를 찾을 수 없습니다 (회사ID: {company_id_str})")
                        continue
                
                # 회사 정보 저장 (TSV에서 직접 가져오거나 Company에서)
                company_name = row['회사명'] if pd.notna(row.get('회사명')) else (company_obj.company_name if company_obj else '')
                company_city_district = row.get('소재지(시/구)', '') if pd.notna(row.get('소재지(시/구)', '')) else (company_obj.city_district if company_obj else '')
                
                # 날짜 변환
                visit_date = None
                if pd.notna(row['방문일자']):
                    try:
                        visit_date = pd.to_datetime(row['방문일자']).date()
                    except:
                        errors.append(f"행 {index + 2}: 방문일자 형식이 올바르지 않습니다: {row['방문일자']}")
                        continue
                
                # 작성일 변환 (TSV의 작성일을 createdAt에 사용, 시간은 00:00:00으로)
                created_at = None
                if '작성일' in row and pd.notna(row['작성일']) and str(row['작성일']).strip():
                    try:
                        # 날짜를 datetime으로 변환하고 시간을 00:00:00으로 설정
                        date_obj = pd.to_datetime(row['작성일']).date()
                        from django.utils import timezone
                        import datetime
                        created_at = timezone.make_aware(datetime.datetime.combine(date_obj, datetime.time.min))
                    except:
                        pass
                
                # 영업단계
                sales_stage = None
                if '영업단계' in row and pd.notna(row['영업단계']) and str(row['영업단계']).strip():
                    sales_stage_str = str(row['영업단계']).strip()
                    # choices에 있는지 확인
                    valid_stages = [choice[0] for choice in Report.SALES_STAGE_CHOICES]
                    if sales_stage_str in valid_stages:
                        sales_stage = sales_stage_str
                
                # 영업형태 검증
                type_str = str(row['영업형태']).strip() if pd.notna(row['영업형태']) else ''
                valid_types = [choice[0] for choice in Report.TYPE_CHOICES]
                if type_str not in valid_types:
                    errors.append(f"행 {index + 2}: 영업형태가 올바르지 않습니다: {type_str}")
                    continue
                
                # 영업일지 생성
                report_data = {
                    'author': author,
                    'author_name': author_name,
                    'author_department': author_department,
                    'visitDate': visit_date,
                    'company_code': company_obj.company_code if company_obj else None,
                    'company_name': company_name,
                    'company_city_district': company_city_district,
                    'sales_stage': sales_stage,
                    'type': type_str,
                    'products': str(row['사용품목']).strip() if pd.notna(row.get('사용품목')) else '',
                    'content': str(row['미팅 내용']).strip() if pd.notna(row.get('미팅 내용')) else '',
                    'tags': str(row['태그']).strip() if pd.notna(row.get('태그')) else '',
                }
                
                report = Report.objects.create(**report_data)
                
                # 작성일이 있으면 업데이트 (시간은 00:00:00으로)
                if created_at:
                    report.createdAt = created_at
                    report.save(update_fields=['createdAt'])
                
                created_count += 1
                    
            except Exception as e:
                errors.append(f"행 {index + 2}: {str(e)}")
                import traceback
                logging.error(f"행 {index + 2} 오류 상세: {traceback.format_exc()}")
                continue
        
        return Response({
            'message': f'영업일지 업로드 완료: {created_count}개 생성, 기존 데이터 {deleted_count}개 삭제됨',
            'created_count': created_count,
            'deleted_count': deleted_count,
            'errors': errors[:20]  # 최대 20개 오류만 반환
        })
        
    except Exception as e:
        logging.error(f'영업일지 CSV/TSV 업로드 오류: {e}')
        import traceback
        logging.error(traceback.format_exc())
        return Response({'error': f'업로드 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_companies_csv(request):
    """회사 CSV 파일을 업로드하여 일괄 업데이트/생성"""
    try:
        # 관리자 권한 확인
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': '관리자만 업로드할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        if 'file' not in request.FILES:
            return Response({'error': '파일이 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        
        # 파일 확장자 확인 및 읽기
        file_extension = csv_file.name.lower().split('.')[-1]
        if file_extension not in ['csv', 'xlsx']:
            return Response({'error': 'CSV 또는 XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(csv_file)
            else:  # xlsx
                df = pd.read_excel(BytesIO(csv_file.read()))
        except Exception as e:
            return Response({'error': f'파일 읽기 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 필요한 컬럼 확인 (필수: 회사코드, 회사명)
        required_columns = ['회사코드', '회사명']
        if not all(col in df.columns for col in required_columns):
            return Response({'error': '파일에 필수 컬럼(회사코드, 회사명)이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = 0
        created_count = 0
        errors = []
        
        def safe_get_value(row, col_name, default=None):
            """안전하게 컬럼 값 가져오기 (빈 문자열은 None으로 변환)"""
            if col_name in df.columns and pd.notna(row[col_name]):
                value = str(row[col_name]).strip()
                return value if value else None
            return default
        
        def safe_get_date(row, col_name):
            """날짜 필드 안전하게 가져오기"""
            if col_name in df.columns and pd.notna(row[col_name]):
                try:
                    return pd.to_datetime(row[col_name]).date()
                except:
                    return None
            return None
        
        for index, row in df.iterrows():
            try:
                company_code = safe_get_value(row, '회사코드')
                company_name = safe_get_value(row, '회사명')
                
                if not company_code or not company_name:
                    errors.append(f"행 {index + 2}: 회사코드와 회사명은 필수입니다.")
                    continue
                
                # 기존 회사 업데이트 또는 새로 생성
                company, created = Company.objects.update_or_create(
                    company_code=company_code,
                    defaults={
                        'company_name': company_name,
                        # 기본정보
                        'customer_classification': safe_get_value(row, '고객분류'),
                        'company_type': safe_get_value(row, '회사유형'),
                        'tax_id': safe_get_value(row, '사업자등록번호'),
                        'established_date': safe_get_date(row, '설립일'),
                        'ceo_name': safe_get_value(row, '대표자명'),
                        'head_address': safe_get_value(row, '본사 주소'),
                        'city_district': safe_get_value(row, '시/구'),
                        'processing_address': safe_get_value(row, '공장 주소'),
                        'main_phone': safe_get_value(row, '대표전화'),
                        'industry_name': safe_get_value(row, '업종명'),
                        'products': safe_get_value(row, '주요제품'),
                        'website': safe_get_value(row, '웹사이트'),
                        'remarks': safe_get_value(row, '참고사항'),
                        # SAP정보
                        'sap_code_type': safe_get_value(row, 'SAP코드여부'),
                        'company_code_sap': safe_get_value(row, 'SAP거래처코드'),
                        'biz_code': safe_get_value(row, '사업'),
                        'biz_name': safe_get_value(row, '사업부'),
                        'department_code': safe_get_value(row, '지점/팀'),
                        'department': safe_get_value(row, '팀명'),
                        'employee_number': safe_get_value(row, '사원번호'),
                        'employee_name': safe_get_value(row, '영업 사원'),
                        'distribution_type_sap_code': safe_get_value(row, '유통형태코드'),
                        'distribution_type_sap': safe_get_value(row, '유통형태'),
                        'contact_person': safe_get_value(row, '거래처 담당자'),
                        'contact_phone': safe_get_value(row, '담당자 연락처'),
                        'code_create_date': safe_get_date(row, '코드생성일'),
                        'transaction_start_date': safe_get_date(row, '거래시작일'),
                        'payment_terms': safe_get_value(row, '결제조건'),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f"행 {index + 2}: {str(e)}")
                continue
        
        return Response({
            'message': f'회사 업로드 완료: {created_count}개 생성, {updated_count}개 업데이트',
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors[:10]  # 최대 10개 오류만 반환
        })
        
    except Exception as e:
        logging.error(f'회사 CSV 업로드 오류: {e}')
        return Response({'error': '업로드 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_sales_data_csv(request):
    """매출 데이터 CSV 업로드"""
    print("=== 매출 데이터 업로드 함수 호출됨 ===")
    print("사용자:", request.user.username if request.user else "비인증")
    print("FILES:", request.FILES)
    try:
        if 'file' not in request.FILES:
            print("오류: 파일이 제공되지 않음")
            return Response({'error': '파일이 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        print(f"업로드된 파일: {csv_file.name}, 크기: {csv_file.size}")
        
        # 파일 확장자 확인
        file_extension = csv_file.name.lower().split('.')[-1]
        if file_extension not in ['csv', 'xlsx', 'tsv']:
            return Response({'error': 'CSV, TSV 또는 XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 읽기 (CSV, TSV 또는 XLSX)
        if file_extension == 'tsv':
            # TSV 파일 읽기
            csv_file.seek(0)  # 파일 포인터를 처음으로
            try:
                df = pd.read_csv(csv_file, sep='\t', encoding='utf-8', keep_default_na=False, na_values=[''])
                # 각 행을 dictionary로 변환
                csv_reader = []
                for _, row in df.iterrows():
                    # NaN 값을 빈 문자열로 변환하고, 숫자 필드는 안전하게 처리
                    dict_row = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.isna(val) or (isinstance(val, str) and val.lower() in ['nan', 'none', 'null']):
                            dict_row[col] = ''
                        else:
                            dict_row[col] = str(val) if val is not None else ''
                    csv_reader.append(dict_row)
            except Exception as e:
                return Response({'error': f'TSV 파일 읽기 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        elif file_extension == 'csv':
            csv_data = csv_file.read().decode('utf-8')
            # 두 번 이상 순회가 필요하므로 리스트로 변환
            csv_reader = [dict(row) for row in csv.DictReader(csv_data.splitlines())]
        else:  # xlsx
            # XLSX 파일을 DataFrame으로 읽어서 dictionary 형태로 변환
            try:
                df = pd.read_excel(BytesIO(csv_file.read()))
                # 각 행을 dictionary로 변환
                csv_reader = []
                for _, row in df.iterrows():
                    # NaN 값을 빈 문자열로 변환
                    dict_row = {}
                    for col in df.columns:
                        dict_row[col] = '' if pd.isna(row[col]) else str(row[col])
                    csv_reader.append(dict_row)
            except Exception as e:
                return Response({'error': f'XLSX 파일 읽기 오류: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_count = 0
        updated_count = 0
        errors = []
        skipped_count = 0
        skipped_reasons = {
            'no_customer_name': 0,
            'no_sale_date': 0,
            'no_sale_amount': 0,
            'invalid_sale_date': 0,
            'invalid_sale_amount': 0,
            'exception': 0
        }
        
        # 덮어쓰기 모드: 파일에 포함된 연-월 단위로 기존 데이터 삭제
        try:
            months_to_overwrite = set()
            for temp_row in csv_reader:
                try:
                    if not temp_row.get('매출일자', '').strip():
                        continue
                    temp_dt = pd.to_datetime(temp_row['매출일자']).date()
                    months_to_overwrite.add((temp_dt.year, temp_dt.month))
                except Exception:
                    # 날짜 파싱 실패 행은 삭제 범위 계산에서 제외
                    continue
            deleted_total = 0
            for y, m in months_to_overwrite:
                deleted_qs = SalesData.objects.filter(매출일자__year=y, 매출일자__month=m)
                deleted_count, _ = deleted_qs.delete()
                deleted_total += deleted_count
            print(f"[덮어쓰기] 삭제 대상 월: {sorted(list(months_to_overwrite))}, 삭제 건수: {deleted_total}")
        except Exception as e:
            print(f"[덮어쓰기] 기존 데이터 삭제 중 오류: {e}")
        
        total_rows = len(csv_reader)
        print(f"[업로드] 총 읽은 행 수: {total_rows}")
        
        for row_num, row in enumerate(csv_reader, start=2):  # 헤더가 1행이므로 2부터 시작
            try:
                # 원본 행 데이터 저장 (디버깅용)
                original_map = dict(row)
                
                # 거래처명 처리 (없으면 기본값 사용)
                거래처명 = row.get('거래처명', '').strip()
                if not 거래처명:
                    거래처명 = f"미지정거래처_{row_num}"
                    skipped_reasons['no_customer_name'] += 1
                
                # 매출일자 파싱 (필수 필드, 없으면 오늘 날짜 사용)
                매출일자 = None
                if row.get('매출일자', '').strip():
                    try:
                        매출일자 = pd.to_datetime(row['매출일자']).date()
                    except:
                        try:
                            # 다양한 날짜 형식 시도
                            매출일자 = pd.to_datetime(row['매출일자'], errors='coerce').date()
                            if pd.isna(매출일자) or 매출일자 is None:
                                skipped_reasons['invalid_sale_date'] += 1
                                errors.append(f"{row_num}행: 매출일자 형식이 올바르지 않아 오늘 날짜로 처리합니다. ({row.get('매출일자', '')})")
                                매출일자 = date.today()
                        except:
                            skipped_reasons['invalid_sale_date'] += 1
                            errors.append(f"{row_num}행: 매출일자 형식이 올바르지 않아 오늘 날짜로 처리합니다. ({row.get('매출일자', '')})")
                            매출일자 = date.today()
                else:
                    skipped_reasons['no_sale_date'] += 1
                    errors.append(f"{row_num}행: 매출일자가 없어 오늘 날짜로 처리합니다.")
                    매출일자 = date.today()
                
                # 매출금액 파싱 (필수 필드, 없으면 0으로 처리)
                매출금액 = 0
                매출금액_raw = row.get('매출금액', '')
                # pandas NaN 체크
                if 매출금액_raw and not pd.isna(매출금액_raw) and str(매출금액_raw).strip():
                    try:
                        매출금액_str = str(매출금액_raw).replace(',', '').replace(' ', '').strip()
                        # NaN 문자열 체크
                        if 매출금액_str.lower() not in ['nan', 'none', '', 'null', 'nat'] and 매출금액_str:
                            매출금액_float = float(매출금액_str)
                            # NaN, Infinity 체크
                            if not pd.isna(매출금액_float) and not np.isnan(매출금액_float) and not np.isinf(매출금액_float):
                                매출금액 = int(매출금액_float)
                            else:
                                raise ValueError("매출금액이 NaN 또는 Infinity입니다")
                    except Exception as e:
                        skipped_reasons['invalid_sale_amount'] += 1
                        errors.append(f"{row_num}행: 매출금액 형식이 올바르지 않습니다. ({row.get('매출금액', '')}) - {str(e)}")
                        # 오류가 있어도 0으로 처리하고 계속 진행
                        매출금액 = 0
                else:
                    skipped_reasons['no_sale_amount'] += 1
                    errors.append(f"{row_num}행: 매출금액이 없어 0으로 처리합니다.")
                    매출금액 = 0
                # 추가 수치 파싱: 매출이익, 매입금액, 매출단가, 매입단가, 이익율
                def parse_int_safe(val):
                    try:
                        # pandas NaN, numpy nan, None 등 먼저 체크
                        if val is None or pd.isna(val) or str(val).strip() == '':
                            return None
                        s = str(val).replace(',', '').replace(' ', '').strip()
                        # NaN, nan, None 등 처리
                        if s.lower() in ['nan', 'none', '', 'null', 'none', 'nat']:
                            return None
                        if s == '':
                            return None
                        # 숫자 변환 시도
                        result = int(float(s))
                        # 변환 후에도 NaN 체크 (float('nan') -> int 변환 시 오류 가능)
                        if pd.isna(result) or np.isnan(result):
                            return None
                        return result
                    except (ValueError, TypeError, OverflowError):
                        return None
                    except Exception:
                        return None

                def parse_float_safe(val):
                    try:
                        # pandas NaN, numpy nan, None 등 먼저 체크
                        if val is None or pd.isna(val) or str(val).strip() == '':
                            return None
                        s = str(val).replace('%', '').replace(',', '').replace(' ', '').strip()
                        # NaN, nan, None 등 처리
                        if s.lower() in ['nan', 'none', '', 'null', 'none', 'nat']:
                            return None
                        if s == '':
                            return None
                        # 숫자 변환 시도
                        result = float(s)
                        # 변환 후에도 NaN 체크
                        if pd.isna(result) or np.isnan(result) or np.isinf(result):
                            return None
                        return result
                    except (ValueError, TypeError, OverflowError):
                        return None
                    except Exception:
                        return None

                # 모든 숫자 필드 파싱 및 검증
                매출이익_val = parse_int_safe(row.get('매출이익'))
                매입금액_val = parse_int_safe(row.get('매입금액'))
                매출단가_val = parse_int_safe(row.get('매출단가'))
                매입단가_val = parse_int_safe(row.get('매입단가'))
                이익율_val = parse_float_safe(row.get('이익율'))
                
                # 매출이익이 없고 매입금액이 있으면 계산: 매출금액 - 매입금액
                if 매출이익_val is None and 매입금액_val is not None:
                    매출이익_val = 매출금액 - 매입금액_val

                # 이익율이 없으면 계산
                if 이익율_val is None and 매출이익_val is not None and 매출금액:
                    try:
                        이익율_val = round((매출이익_val / 매출금액) * 100, 2)
                    except Exception:
                        이익율_val = None
                
                # Box 파싱 (있는 경우만)
                Box = None
                box_val = row.get('Box', '')
                if box_val and not pd.isna(box_val) and str(box_val).strip():
                    try:
                        box_str = str(box_val).replace(',', '').replace(' ', '').strip()
                        # NaN, nan, None 등 처리
                        if box_str.lower() not in ['nan', 'none', '', 'null', 'nat'] and box_str:
                            box_result = int(float(box_str))
                            # NaN 체크
                            if not pd.isna(box_result) and not np.isnan(box_result):
                                Box = box_result
                    except:
                        Box = None
                
                # 중량 파싱 (있는 경우만)
                중량_Kg = None
                weight_val = row.get('중량(Kg)', '')
                if weight_val and not pd.isna(weight_val) and str(weight_val).strip():
                    try:
                        weight_str = str(weight_val).replace(',', '').replace(' ', '').strip()
                        # NaN, nan, None 등 처리
                        if weight_str.lower() not in ['nan', 'none', '', 'null', 'nat'] and weight_str:
                            weight_result = float(weight_str)
                            # NaN, Infinity 체크
                            if not pd.isna(weight_result) and not np.isnan(weight_result) and not np.isinf(weight_result):
                                중량_Kg = weight_result
                    except:
                        중량_Kg = None
                
                # 매입일자 파싱 (있는 경우만)
                매입일자 = None
                if row.get('매입일자', '').strip():
                    try:
                        매입일자 = pd.to_datetime(row['매입일자']).date()
                    except:
                        pass
                
                # 재고보유일 파싱 (있는 경우만)
                재고보유일 = None
                재고보유일_val = row.get('재고보유일', '')
                if 재고보유일_val and not pd.isna(재고보유일_val):
                    재고보유일_str = str(재고보유일_val).strip().replace(',', '').replace(' ', '')
                    if 재고보유일_str and 재고보유일_str.lower() not in ['nan', 'none', 'null', 'nat']:
                        try:
                            재고보유일_float = float(재고보유일_str)
                            if not pd.isna(재고보유일_float) and not np.isnan(재고보유일_float):
                                재고보유일 = int(재고보유일_float)
                        except Exception:
                            재고보유일 = None
                
                # 타입 최종 검증 및 정리 (모든 파싱 완료 후)
                # NaN 값 체크 및 None 변환
                if 매출이익_val is not None:
                    if pd.isna(매출이익_val) or np.isnan(매출이익_val) or not isinstance(매출이익_val, (int, float)):
                        try:
                            if pd.isna(매출이익_val) or np.isnan(매출이익_val):
                                매출이익_val = None
                            elif isinstance(매출이익_val, (float, int)):
                                매출이익_val = int(매출이익_val) if not pd.isna(매출이익_val) else None
                            else:
                                매출이익_val = None
                        except Exception:
                            매출이익_val = None

                if 매입금액_val is not None:
                    if pd.isna(매입금액_val) or np.isnan(매입금액_val) or not isinstance(매입금액_val, (int, float)):
                        try:
                            if pd.isna(매입금액_val) or np.isnan(매입금액_val):
                                매입금액_val = None
                            elif isinstance(매입금액_val, (float, int)):
                                매입금액_val = int(매입금액_val) if not pd.isna(매입금액_val) else None
                            else:
                                매입금액_val = None
                        except Exception:
                            매입금액_val = None

                if 매출단가_val is not None:
                    if pd.isna(매출단가_val) or np.isnan(매출단가_val) or not isinstance(매출단가_val, (int, float)):
                        try:
                            if pd.isna(매출단가_val) or np.isnan(매출단가_val):
                                매출단가_val = None
                            elif isinstance(매출단가_val, (float, int)):
                                매출단가_val = int(매출단가_val) if not pd.isna(매출단가_val) else None
                            else:
                                매출단가_val = None
                        except Exception:
                            매출단가_val = None

                if 매입단가_val is not None:
                    if pd.isna(매입단가_val) or np.isnan(매입단가_val) or not isinstance(매입단가_val, (int, float)):
                        try:
                            if pd.isna(매입단가_val) or np.isnan(매입단가_val):
                                매입단가_val = None
                            elif isinstance(매입단가_val, (float, int)):
                                매입단가_val = int(매입단가_val) if not pd.isna(매입단가_val) else None
                            else:
                                매입단가_val = None
                        except Exception:
                            매입단가_val = None

                if 이익율_val is not None:
                    if pd.isna(이익율_val) or np.isnan(이익율_val) or np.isinf(이익율_val) or not isinstance(이익율_val, (float, int)):
                        try:
                            if pd.isna(이익율_val) or np.isnan(이익율_val) or np.isinf(이익율_val):
                                이익율_val = None
                            elif isinstance(이익율_val, (float, int)):
                                이익율_val = float(이익율_val) if not (pd.isna(이익율_val) or np.isnan(이익율_val) or np.isinf(이익율_val)) else None
                            else:
                                이익율_val = None
                        except Exception:
                            이익율_val = None

                if Box is not None:
                    if pd.isna(Box) or np.isnan(Box) or not isinstance(Box, (int, float)):
                        try:
                            if pd.isna(Box) or np.isnan(Box):
                                Box = None
                            elif isinstance(Box, (float, int)):
                                Box = int(Box) if not pd.isna(Box) else None
                            else:
                                Box = None
                        except Exception:
                            Box = None

                if 중량_Kg is not None:
                    if pd.isna(중량_Kg) or np.isnan(중량_Kg) or np.isinf(중량_Kg) or not isinstance(중량_Kg, (float, int)):
                        try:
                            if pd.isna(중량_Kg) or np.isnan(중량_Kg) or np.isinf(중량_Kg):
                                중량_Kg = None
                            elif isinstance(중량_Kg, (float, int)):
                                중량_Kg = float(중량_Kg) if not (pd.isna(중량_Kg) or np.isnan(중량_Kg) or np.isinf(중량_Kg)) else None
                            else:
                                중량_Kg = None
                        except Exception:
                            중량_Kg = None

                if 재고보유일 is not None:
                    if pd.isna(재고보유일) or np.isnan(재고보유일) or not isinstance(재고보유일, (int, float)):
                        try:
                            if pd.isna(재고보유일) or np.isnan(재고보유일):
                                재고보유일 = None
                            elif isinstance(재고보유일, (float, int)):
                                재고보유일 = int(재고보유일) if not pd.isna(재고보유일) else None
                            else:
                                재고보유일 = None
                        except Exception:
                            재고보유일 = None

                # 매출금액은 필수 필드이므로 0으로 기본값 설정
                if not isinstance(매출금액, int) or pd.isna(매출금액) or np.isnan(매출금액):
                    try:
                        if pd.isna(매출금액) or np.isnan(매출금액):
                            매출금액 = 0
                        else:
                            매출금액 = int(매출금액) if 매출금액 else 0
                    except Exception:
                        매출금액 = 0
                
                # 저장 직전 최종 NaN 체크 및 값 정리 함수 정의
                def safe_int_value(val):
                    """정수 값 안전하게 정리 (NaN 체크 포함)"""
                    if val is None:
                        return None
                    try:
                        # pandas/numpy NaN 체크 (문자열 변환 전에 체크)
                        try:
                            if pd.isna(val):
                                return None
                        except (TypeError, ValueError):
                            pass
                        try:
                            if isinstance(val, (float, int)) and np.isnan(val):
                                return None
                        except (TypeError, ValueError):
                            pass
                        
                        # 문자열인 경우 숫자로 변환 시도
                        if isinstance(val, str):
                            val = val.strip().replace(',', '').replace(' ', '')
                            if val.lower() in ['nan', 'none', '', 'null', 'nat', 'none']:
                                return None
                            val = float(val)
                        
                        # 숫자 타입으로 변환
                        if isinstance(val, (int, float)):
                            result = int(val)
                            # 변환 후 NaN 체크
                            try:
                                if pd.isna(result) or (isinstance(result, float) and np.isnan(result)):
                                    return None
                            except (TypeError, ValueError):
                                pass
                            return result
                        return None
                    except (ValueError, TypeError, OverflowError):
                        return None
                    except Exception:
                        return None
                
                def safe_float_value(val):
                    """실수 값 안전하게 정리 (NaN, Infinity 체크 포함)"""
                    if val is None:
                        return None
                    try:
                        # pandas/numpy NaN 체크 (문자열 변환 전에 체크)
                        try:
                            if pd.isna(val):
                                return None
                        except (TypeError, ValueError):
                            pass
                        try:
                            if isinstance(val, (float, int)) and (np.isnan(val) or np.isinf(val)):
                                return None
                        except (TypeError, ValueError):
                            pass
                        
                        # 문자열인 경우 숫자로 변환 시도
                        if isinstance(val, str):
                            val = val.strip().replace(',', '').replace(' ', '').replace('%', '')
                            if val.lower() in ['nan', 'none', '', 'null', 'nat', 'none']:
                                return None
                            val = float(val)
                        
                        # 숫자 타입으로 변환
                        if isinstance(val, (int, float)):
                            result = float(val)
                            # 변환 후 NaN, Infinity 체크
                            try:
                                if pd.isna(result) or np.isnan(result) or np.isinf(result):
                                    return None
                            except (TypeError, ValueError):
                                pass
                            return result
                        return None
                    except (ValueError, TypeError, OverflowError):
                        return None
                    except Exception:
                        return None
                
                # 각 행을 항상 개별 매출로 저장 (중복 병합 금지)
                # 최종 값 정리
                Box_final = safe_int_value(Box)
                매출단가_final = safe_int_value(매출단가_val)
                매출이익_final = safe_int_value(매출이익_val)
                매입단가_final = safe_int_value(매입단가_val)
                매입금액_final = safe_int_value(매입금액_val)
                재고보유일_final = safe_int_value(재고보유일)
                중량_Kg_final = safe_float_value(중량_Kg)
                이익율_final = safe_float_value(이익율_val)
                # 매출금액은 필수 필드이므로 None이면 0으로 설정
                매출금액_final = safe_int_value(매출금액) if 매출금액 is not None else 0
                if 매출금액_final is None:
                    매출금액_final = 0
                
                # 최종 타입 검증 - Oracle에 전달하기 전에 모든 값이 올바른 타입인지 확인
                # None이 아닌 경우 반드시 숫자 타입이어야 함
                if Box_final is not None and not isinstance(Box_final, int):
                    Box_final = None
                if 매출단가_final is not None and not isinstance(매출단가_final, int):
                    매출단가_final = None
                if 매출이익_final is not None and not isinstance(매출이익_final, int):
                    매출이익_final = None
                if 매입단가_final is not None and not isinstance(매입단가_final, int):
                    매입단가_final = None
                if 매입금액_final is not None and not isinstance(매입금액_final, int):
                    매입금액_final = None
                if 재고보유일_final is not None and not isinstance(재고보유일_final, int):
                    재고보유일_final = None
                if 중량_Kg_final is not None and not isinstance(중량_Kg_final, (int, float)):
                    중량_Kg_final = None
                if 이익율_final is not None and not isinstance(이익율_final, (int, float)):
                    이익율_final = None
                if not isinstance(매출금액_final, int):
                    매출금액_final = 0
                
                # 모든 숫자 필드가 올바른 타입인지 최종 검증
                # 코드 필드는 문자열로 변환 (숫자로 들어올 수 있음)
                코드값 = row.get('코드', '')
                if 코드값:
                    try:
                        코드값 = str(코드값).strip()
                        if 코드값.lower() in ['nan', 'none', '', 'null', 'nat']:
                            코드값 = None
                        else:
                            코드값 = 코드값 or None
                    except:
                        코드값 = None
                else:
                    코드값 = None
                
                try:
                    # 저장 전 최종 검증 - 모든 숫자 값이 올바른 타입인지 확인
                    # Oracle은 NaN, Infinity 등을 허용하지 않으므로 엄격하게 체크
                    # 문자열 필드도 안전하게 처리
                    def safe_str_value(val, max_length=None):
                        """문자열 값 안전하게 정리"""
                        if val is None:
                            return None
                        try:
                            if pd.isna(val):
                                return None
                            s = str(val).strip()
                            if s.lower() in ['nan', 'none', '', 'null', 'nat']:
                                return None
                            if max_length and len(s) > max_length:
                                s = s[:max_length]
                            return s or None
                        except:
                            return None

                    def describe_field(field_name, value, original=None):
                        """디버깅용 필드 설명 문자열 생성"""
                        value_type = type(value).__name__ if value is not None else 'None'
                        original_type = type(original).__name__ if original is not None else 'None'
                        original_info = f" | 원본: {original} (타입: {original_type})"
                        try:
                            field_meta = SalesData._meta.get_field(field_name)
                            field_class = field_meta.__class__.__name__
                            db_type = field_meta.db_type(connection)
                            field_info = f" | 모델필드: {field_class} | DB타입: {db_type}"
                        except Exception:
                            field_info = ''
                        return f"    {field_name}: {value} (타입: {value_type}){original_info}{field_info}"

                    create_params = {
                        '매출일자': 매출일자,
                        '코드': safe_str_value(코드값, max_length=50),
                        '거래처명': 거래처명,
                        '매출부서': safe_str_value(row.get('매출부서', ''), max_length=100),
                        '매출담당자': safe_str_value(row.get('매출담당자', ''), max_length=100),
                        '유통형태': safe_str_value(row.get('유통형태', ''), max_length=100),
                        '상품코드': safe_str_value(row.get('상품코드', ''), max_length=100),
                        '상품명': safe_str_value(row.get('상품명', ''), max_length=200),
                        '브랜드': safe_str_value(row.get('브랜드', ''), max_length=100),
                        '축종': safe_str_value(row.get('축종', ''), max_length=100),
                        '부위': safe_str_value(row.get('부위', ''), max_length=100),
                        '원산지': safe_str_value(row.get('원산지', ''), max_length=100),
                        '축종_부위': safe_str_value(row.get('축종-부위', ''), max_length=100),
                        '원산지_축종': safe_str_value(row.get('원산지', ''), max_length=100),
                        '등급': safe_str_value(row.get('등급', ''), max_length=50),
                        'Box': Box_final,
                        '중량_Kg': 중량_Kg_final,
                        '매출단가': 매출단가_final,
                        '매출금액': 매출금액_final,
                        '매출이익': 매출이익_final,
                        '이익율': 이익율_final,
                        '매입처': safe_str_value(row.get('매 입 처', row.get('매입 처', '')), max_length=200),
                        '매입일자': 매입일자,
                        '재고보유일': 재고보유일_final,
                        '수입로컬': safe_str_value(row.get('수입/로컬', ''), max_length=20),
                        '이관재고여부': safe_str_value(row.get('이관재고 여부', ''), max_length=20),
                        '담당자': safe_str_value(row.get('담당자', ''), max_length=100),
                        '매입단가': 매입단가_final,
                        '매입금액': 매입금액_final,
                        '지점명': safe_str_value(row.get('지점명', ''), max_length=100),
                        '매출비고': safe_str_value(row.get('매출비고', '')),
                        '매입비고': safe_str_value(row.get('매입비고', '')),
                        '이력번호': safe_str_value(row.get('이력번호', ''), max_length=100),
                        'BL번호': safe_str_value(row.get('B/L번호(도체번호)', ''), max_length=100),
                    }
                    
                    # 저장 전 모든 파라미터 타입 확인 및 로깅
                    print(f"[디버깅] {row_num}행: 첫 번째 저장 시도 - 모든 필드 값:")
                    print(f"  [원본 파싱된 값]")
                    print(describe_field('Box 원본', Box))
                    print(describe_field('중량_Kg 원본', 중량_Kg))
                    print(describe_field('매출단가 원본', 매출단가_val))
                    print(describe_field('매출금액 원본', 매출금액))
                    print(describe_field('매출이익 원본', 매출이익_val))
                    print(describe_field('이익율 원본', 이익율_val))
                    print(describe_field('매입단가 원본', 매입단가_val))
                    print(describe_field('매입금액 원본', 매입금액_val))
                    print(describe_field('재고보유일 원본', 재고보유일))
                    print(f"  [검증 후 최종 값]")
                    for key, val in create_params.items():
                        original_val = None
                        if key == 'Box':
                            original_val = Box
                        elif key == '중량_Kg':
                            original_val = 중량_Kg
                        elif key == '매출단가':
                            original_val = 매출단가_val
                        elif key == '매출금액':
                            original_val = 매출금액
                        elif key == '매출이익':
                            original_val = 매출이익_val
                        elif key == '이익율':
                            original_val = 이익율_val
                        elif key == '재고보유일':
                            original_val = 재고보유일
                        elif key == '매입단가':
                            original_val = 매입단가_val
                        elif key == '매입금액':
                            original_val = 매입금액_val
                        print(describe_field(key, val, original_val))
                    
                    # 저장 전 최종 검증 - 모든 필드가 올바른 타입인지 확인
                    # 특히 이익율이 0.0일 때도 올바르게 저장되도록 보장
                    # 중복 키 확인
                    create_params_keys = list(create_params.keys())
                    if len(create_params_keys) != len(set(create_params_keys)):
                        duplicates = [k for k in create_params_keys if create_params_keys.count(k) > 1]
                        print(f"[경고] {row_num}행: create_params에 중복된 키 발견: {set(duplicates)}")
                    
                    final_params = {}
                    for key, val in create_params.items():
                        # 중복 키 방지
                        if key in final_params:
                            print(f"[경고] {row_num}행: 중복된 키 발견: {key}, 기존 값: {final_params[key]}, 새 값: {val}")
                            continue
                        
                        if key == '이익율' and val == 0.0:
                            # 이익율이 0.0인 경우 명시적으로 float로 변환하여 저장
                            final_params[key] = 0.0
                        elif key in ['Box', '중량_Kg', '매출단가', '매출금액', '매출이익', '이익율', '매입단가', '매입금액', '재고보유일']:
                            # 숫자 필드는 타입 재확인
                            if val is not None:
                                try:
                                    if key in ['Box', '매출단가', '매출이익', '매입단가', '매입금액', '재고보유일']:
                                        # 정수 필드
                                        if isinstance(val, (int, float)):
                                            if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                                final_params[key] = None
                                            else:
                                                final_params[key] = int(val)
                                        else:
                                            final_params[key] = None
                                    elif key == '매출금액':
                                        # 매출금액은 필수 필드
                                        if isinstance(val, (int, float)):
                                            if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                                final_params[key] = 0
                                            else:
                                                final_params[key] = int(val)
                                        else:
                                            final_params[key] = 0
                                    elif key in ['중량_Kg', '이익율']:
                                        # 실수 필드
                                        if isinstance(val, (int, float)):
                                            if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                                                final_params[key] = None
                                            else:
                                                final_params[key] = float(val)
                                        else:
                                            final_params[key] = None
                                    else:
                                        final_params[key] = val
                                except Exception as e:
                                    print(f"[경고] {row_num}행: {key} 필드 최종 검증 중 오류: {str(e)}")
                                    final_params[key] = None if key != '매출금액' else 0
                            else:
                                final_params[key] = None if key != '매출금액' else 0
                        else:
                            final_params[key] = val
                    
                    SalesData.objects.create(**final_params)

                    created_count += 1
                except Exception as create_error:
                    # 생성 실패 시 오류 상세 정보 출력
                    error_str = str(create_error)
                    print(f"[디버깅] {row_num}행: 첫 번째 저장 시도 실패")
                    print(f"  오류 메시지: {error_str}")
                    print(f"  오류 타입: {type(create_error).__name__}")
                    debug_all_fields(row_num, '최종 저장 파라미터 (예외 발생 시)', final_params if 'final_params' in locals() else create_params, original_map)
                    
                    # ORA-01722 오류인 경우, 어떤 필드가 문제인지 추정
                    if 'ORA-01722' in error_str or '수치가 부적합합니다' in error_str:
                        print(f"  [ORA-01722 디버깅] 문제 필드 찾기 시작...")
                        print(f"  [원본 파싱된 값 - 재확인]")
                        print(f"    Box 원본: {Box} (타입: {type(Box).__name__ if Box is not None else 'None'})")
                        print(f"    중량_Kg 원본: {중량_Kg} (타입: {type(중량_Kg).__name__ if 중량_Kg is not None else 'None'})")
                        print(f"    매출단가 원본: {매출단가_val} (타입: {type(매출단가_val).__name__ if 매출단가_val is not None else 'None'})")
                        print(f"    매출금액 원본: {매출금액} (타입: {type(매출금액).__name__ if 매출금액 is not None else 'None'})")
                        print(f"    매출이익 원본: {매출이익_val} (타입: {type(매출이익_val).__name__ if 매출이익_val is not None else 'None'})")
                        print(f"    이익율 원본: {이익율_val} (타입: {type(이익율_val).__name__ if 이익율_val is not None else 'None'})")
                        print(f"    매입단가 원본: {매입단가_val} (타입: {type(매입단가_val).__name__ if 매입단가_val is not None else 'None'})")
                        print(f"    매입금액 원본: {매입금액_val} (타입: {type(매입금액_val).__name__ if 매입금액_val is not None else 'None'})")
                        print(f"    재고보유일 원본: {재고보유일} (타입: {type(재고보유일).__name__ if 재고보유일 is not None else 'None'})")
                        print(f"  [검증 후 최종 값]")
                        for key, val in create_params.items():
                            if key in ['Box', '중량_Kg', '매출단가', '매출금액', '매출이익', '이익율', '매입단가', '매입금액', '재고보유일']:
                                print(f"    {key}: {val} (타입: {type(val).__name__ if val is not None else 'None'})")
                        
                        # 각 필드를 하나씩 제거하면서 테스트하여 문제 필드 찾기
                        print(f"  [필드별 검증 시작] 각 필드를 하나씩 제거하여 테스트...")
                        from django.db import connection
                        from django.core.exceptions import ValidationError
                        
                        # 숫자 필드 목록 (ORA-01722는 주로 숫자 필드에서 발생하지만, 모든 필드 확인)
                        numeric_fields = ['Box', '중량_Kg', '매출단가', '매출금액', '매출이익', '이익율', '매입단가', '매입금액', '재고보유일']
                        
                        # final_params 복사본 생성
                        test_params = final_params.copy()
                        
                        # 각 숫자 필드를 하나씩 제거하면서 테스트
                        found_issue = False
                        for field_name in numeric_fields:
                            if field_name not in test_params:
                                continue
                            
                            # 해당 필드를 제거
                            original_value = test_params.pop(field_name, None)
                            
                            try:
                                # 필드를 제거한 상태로 INSERT 시도
                                test_obj = SalesData(**test_params)
                                test_obj.save()
                                
                                # 성공하면 해당 필드가 문제
                                print(f"    ✓ {field_name} 필드를 제거하니 성공! -> {field_name} 필드가 문제입니다!")
                                print(f"      문제 값: {original_value} (타입: {type(original_value).__name__ if original_value is not None else 'None'})")
                                
                                # 테스트 객체 삭제
                                test_obj.delete()
                                
                                # 문제 필드 찾았으므로 중단
                                found_issue = True
                                break
                            except Exception as test_error:
                                # 실패하면 해당 필드가 문제가 아님
                                error_msg = str(test_error)
                                if 'ORA-01722' in error_msg or '수치가 부적합합니다' in error_msg:
                                    print(f"    ✗ {field_name} 필드를 제거해도 여전히 오류 발생 -> {field_name}은 문제가 아닙니다")
                                else:
                                    print(f"    ✗ {field_name} 필드를 제거했을 때 다른 오류 발생: {error_msg[:100]}")
                                
                                # 다시 필드 복원
                                test_params[field_name] = original_value
                        
                        # 숫자 필드에서 문제를 찾지 못한 경우, 다른 필드들도 확인
                        if not found_issue:
                            print(f"  [경고] 숫자 필드를 하나씩 제거해도 문제를 찾지 못했습니다.")
                            print(f"  [추가 디버깅] 모든 필드의 실제 타입과 값 확인:")
                            for key, val in final_params.items():
                                try:
                                    field_meta = SalesData._meta.get_field(key)
                                    field_type = field_meta.__class__.__name__
                                    db_type = field_meta.db_type(connection)
                                    print(f"    {key}: 값={repr(val)} | 타입={type(val).__name__} | 모델필드={field_type} | DB타입={db_type}")
                                except Exception as e:
                                    print(f"    {key}: 값={repr(val)} | 타입={type(val).__name__} | 모델필드 정보 없음: {str(e)}")
                            
                            # SQL 쿼리 직접 확인
                            print(f"  [SQL 쿼리 분석] 생성된 SQL 쿼리 확인:")
                            try:
                                from django.db.models.sql import compiler
                                obj = SalesData(**final_params)
                                compiler = compiler.SQLInsertCompiler(obj.__class__.objects.query, connection)
                                sql, params = compiler.as_sql()
                                print(f"    SQL: {sql[:500]}...")
                                print(f"    Params: {params[:20]}...")
                            except Exception as sql_error:
                                print(f"    SQL 분석 실패: {str(sql_error)}")
                    
                    # 생성 실패 시 재시도 - 검증된 값이 있으면 사용, 없으면 원본 값으로 재검증
                    try:
                        # 재시도 시 원본 값들을 다시 안전하게 처리
                        def safe_retry_int(val, field_name):
                            """재시도용 정수 값 안전 처리"""
                            if val is None:
                                return None
                            try:
                                if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                    return None
                                if isinstance(val, (int, float)):
                                    result = int(val)
                                    if pd.isna(result) or np.isnan(result):
                                        return None
                                    return result
                                return None
                            except:
                                return None
                        
                        def safe_retry_float(val, field_name):
                            """재시도용 실수 값 안전 처리 (0.0도 유효)"""
                            if val is None:
                                return None
                            try:
                                if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                                    return None
                                if isinstance(val, (int, float)):
                                    result = float(val)
                                    if pd.isna(result) or np.isnan(result) or np.isinf(result):
                                        return None
                                    return result
                                return None
                            except:
                                return None
                        
                        # 재시도용 안전한 값 생성
                        Box_retry = safe_retry_int(Box, 'Box')
                        중량_Kg_retry = safe_retry_float(중량_Kg, '중량_Kg')
                        매출단가_retry = safe_retry_int(매출단가_val, '매출단가')
                        매출금액_retry = safe_retry_int(매출금액, '매출금액') or 0
                        매출이익_retry = safe_retry_int(매출이익_val, '매출이익')
                        이익율_retry = safe_retry_float(이익율_val, '이익율')  # 0.0도 유효
                        매입단가_retry = safe_retry_int(매입단가_val, '매입단가')
                        매입금액_retry = safe_retry_int(매입금액_val, '매입금액')
                        재고보유일_retry = safe_retry_int(재고보유일, '재고보유일')
                        
                        # 재시도용 안전한 create_params 생성 (문자열 필드도 안전하게 처리)
                        retry_params = {
                            '매출일자': 매출일자,
                            '코드': safe_str_value(코드값, max_length=50),
                            '거래처명': 거래처명,
                            '매출부서': safe_str_value(row.get('매출부서', ''), max_length=100),
                            '매출담당자': safe_str_value(row.get('매출담당자', ''), max_length=100),
                            '유통형태': safe_str_value(row.get('유통형태', ''), max_length=100),
                            '상품코드': safe_str_value(row.get('상품코드', ''), max_length=100),
                            '상품명': safe_str_value(row.get('상품명', ''), max_length=200),
                            '브랜드': safe_str_value(row.get('브랜드', ''), max_length=100),
                            '축종': safe_str_value(row.get('축종', ''), max_length=100),
                            '부위': safe_str_value(row.get('부위', ''), max_length=100),
                            '원산지': safe_str_value(row.get('원산지', ''), max_length=100),
                            '축종_부위': safe_str_value(row.get('축종-부위', ''), max_length=100),
                            '원산지_축종': safe_str_value(row.get('원산지', ''), max_length=100),
                            '등급': safe_str_value(row.get('등급', ''), max_length=50),
                            'Box': Box_retry,
                            '중량_Kg': 중량_Kg_retry,
                            '매출단가': 매출단가_retry,
                            '매출금액': 매출금액_retry,
                            '매출이익': 매출이익_retry,
                            '이익율': 이익율_retry,
                            '매입처': safe_str_value(row.get('매 입 처', row.get('매입 처', '')), max_length=200),
                            '매입일자': 매입일자,
                            '재고보유일': 재고보유일_retry,
                            '수입로컬': safe_str_value(row.get('수입/로컬', ''), max_length=20),
                            '이관재고여부': safe_str_value(row.get('이관재고 여부', ''), max_length=20),
                            '담당자': safe_str_value(row.get('담당자', ''), max_length=100),
                            '매입단가': 매입단가_retry,
                            '매입금액': 매입금액_retry,
                            '지점명': safe_str_value(row.get('지점명', ''), max_length=100),
                            '매출비고': safe_str_value(row.get('매출비고', '')),
                            '매입비고': safe_str_value(row.get('매입비고', '')),
                            '이력번호': safe_str_value(row.get('이력번호', ''), max_length=100),
                            'BL번호': safe_str_value(row.get('B/L번호(도체번호)', ''), max_length=100),
                        }
                        
                        # 재시도 전 디버깅 정보 출력
                        print(f"[디버깅] {row_num}행: 재시도 저장 시도 - 모든 필드 값:")
                        print(f"  [원본 파싱된 값]")
                        print(describe_field('Box 원본', Box))
                        print(describe_field('중량_Kg 원본', 중량_Kg))
                        print(describe_field('매출단가 원본', 매출단가_val))
                        print(describe_field('매출금액 원본', 매출금액))
                        print(describe_field('매출이익 원본', 매출이익_val))
                        print(describe_field('이익율 원본', 이익율_val))
                        print(describe_field('매입단가 원본', 매입단가_val))
                        print(describe_field('매입금액 원본', 매입금액_val))
                        print(describe_field('재고보유일 원본', 재고보유일))
                        print(f"  [재시도 파라미터 값]")
                        for key, val in retry_params.items():
                            original_val = None
                            if key == 'Box': original_val = Box
                            elif key == '중량_Kg': original_val = 중량_Kg
                            elif key == '매출단가': original_val = 매출단가_val
                            elif key == '매출금액': original_val = 매출금액
                            elif key == '매출이익': original_val = 매출이익_val
                            elif key == '이익율': original_val = 이익율_val
                            elif key == '재고보유일': original_val = 재고보유일
                            elif key == '매입단가': original_val = 매입단가_val
                            elif key == '매입금액': original_val = 매입금액_val
                            print(describe_field(key, val, original_val))
                        
                        # 재시도 전 최종 검증 - 모든 필드가 올바른 타입인지 확인
                        retry_final_params = {}
                        for key, val in retry_params.items():
                            # 중복 키 방지
                            if key in retry_final_params:
                                print(f"[경고] {row_num}행: 재시도 중복된 키 발견: {key}, 기존 값: {retry_final_params[key]}, 새 값: {val}")
                                continue
                            
                            if key == '이익율' and val == 0.0:
                                # 이익율이 0.0인 경우 명시적으로 float로 변환하여 저장
                                retry_final_params[key] = 0.0
                            elif key in ['Box', '중량_Kg', '매출단가', '매출금액', '매출이익', '이익율', '매입단가', '매입금액', '재고보유일']:
                                # 숫자 필드는 타입 재확인
                                if val is not None:
                                    try:
                                        if key in ['Box', '매출단가', '매출이익', '매입단가', '매입금액', '재고보유일']:
                                            # 정수 필드
                                            if isinstance(val, (int, float)):
                                                if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                                    retry_final_params[key] = None
                                                else:
                                                    retry_final_params[key] = int(val)
                                            else:
                                                retry_final_params[key] = None
                                        elif key == '매출금액':
                                            # 매출금액은 필수 필드
                                            if isinstance(val, (int, float)):
                                                if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                                    retry_final_params[key] = 0
                                                else:
                                                    retry_final_params[key] = int(val)
                                            else:
                                                retry_final_params[key] = 0
                                        elif key in ['중량_Kg', '이익율']:
                                            # 실수 필드
                                            if isinstance(val, (int, float)):
                                                if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                                                    retry_final_params[key] = None
                                                else:
                                                    retry_final_params[key] = float(val)
                                            else:
                                                retry_final_params[key] = None
                                        else:
                                            retry_final_params[key] = val
                                    except Exception as e:
                                        print(f"[경고] {row_num}행: 재시도 {key} 필드 최종 검증 중 오류: {str(e)}")
                                        retry_final_params[key] = None if key != '매출금액' else 0
                                else:
                                    retry_final_params[key] = None if key != '매출금액' else 0
                            else:
                                retry_final_params[key] = val
                        
                        SalesData.objects.create(**retry_final_params)
                        created_count += 1
                        errors.append(f"{row_num}행: 일부 숫자 필드 오류로 기본값으로 저장했습니다. (원본 오류: {str(create_error)})")
                    except Exception as retry_error:
                        # 재시도도 실패하면 스킵 - 오류를 다시 발생시키지 않고 로그만 남김
                        retry_error_str = str(retry_error)
                        print(f"[디버깅] {row_num}행: 재시도 저장 시도도 실패")
                        print(f"  재시도 오류 메시지: {retry_error_str}")
                        print(f"  재시도 오류 타입: {type(retry_error).__name__}")
                        
                        # ORA-01722 오류인 경우, 어떤 필드가 문제인지 추정
                        if 'ORA-01722' in retry_error_str or '수치가 부적합합니다' in retry_error_str:
                            print(f"  [재시도 문제 필드 추정] 숫자 필드 값 재확인:")
                            for key, val in retry_params.items():
                                if key in ['Box', '중량_Kg', '매출단가', '매출금액', '매출이익', '이익율', '매입단가', '매입금액', '재고보유일']:
                                    if val is not None:
                                        try:
                                            # 값이 숫자 타입인지 확인
                                            if not isinstance(val, (int, float)):
                                                print(f"    ⚠️ {key}: {val} (잘못된 타입: {type(val).__name__})")
                                            elif isinstance(val, float) and (pd.isna(val) or np.isnan(val) or np.isinf(val)):
                                                print(f"    ⚠️ {key}: {val} (NaN 또는 Infinity)")
                                            else:
                                                print(f"    ✓ {key}: {val} (타입: {type(val).__name__})")
                                        except Exception as e:
                                            print(f"    ⚠️ {key}: 검증 중 오류 - {str(e)}")
                                    else:
                                        print(f"    - {key}: None")
                        
                        skipped_count += 1
                        skipped_reasons['exception'] += 1
                        import traceback
                        error_detail = traceback.format_exc()
                        error_msg = f"{row_num}행: 재시도도 실패하여 건너뜁니다. (원본 오류: {str(create_error)}, 재시도 오류: {str(retry_error)})"
                        errors.append(error_msg)
                        print(f"[오류] {error_msg}")
                        print(f"  재시도 오류 상세:\n{error_detail}")
            
            except Exception as e:
                skipped_count += 1
                skipped_reasons['exception'] += 1
                import traceback
                error_detail = traceback.format_exc()
                print(f"[오류] {row_num}행 처리 중 예외 발생:")
                print(f"  오류 메시지: {str(e)}")
                print(f"  오류 상세:\n{error_detail}")
                print(f"  행 데이터: 거래처명={row.get('거래처명', '')}, 매출일자={row.get('매출일자', '')}, 매출금액={row.get('매출금액', '')}")
                # 변수가 정의되지 않았을 수 있으므로 안전하게 참조
                try:
                    매출금액_val = 매출금액
                except NameError:
                    매출금액_val = '정의되지 않음'
                try:
                    Box_val = Box
                except NameError:
                    Box_val = '정의되지 않음'
                try:
                    중량_Kg_val = 중량_Kg
                except NameError:
                    중량_Kg_val = '정의되지 않음'
                try:
                    재고보유일_val = 재고보유일
                except NameError:
                    재고보유일_val = '정의되지 않음'
                print(f"  파싱된 값: 매출금액={매출금액_val}, Box={Box_val}, 중량_Kg={중량_Kg_val}, 재고보유일={재고보유일_val}")
                errors.append(f"{row_num}행: {str(e)}")
                continue
        
        print(f"[업로드] 총 행 수: {total_rows}, 생성: {created_count}, 건너뛴 행: {skipped_count}")
        print(f"[업로드] 건너뛴 이유: {skipped_reasons}")
        
        return Response({
            'message': f'매출 데이터 업로드 완료. 신규 생성: {created_count}건, 업데이트: {updated_count}건, 건너뛴 행: {skipped_count}건',
            'created_count': created_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'skipped_reasons': skipped_reasons,
            'total_rows': total_rows,
            'errors': errors[:50]  # 오류 최대 50개만 반환
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[업로드 오류] CSV 업로드 중 예외 발생:")
        print(f"  오류 메시지: {str(e)}")
        print(f"  오류 타입: {type(e).__name__}")
        print(f"  상세 오류:\n{error_detail}")
        return Response(
            {'error': f'CSV 업로드 중 오류가 발생했습니다: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_unique_products(request, company_id):
    """특정 회사의 판매데이터에서 유니크한 상품명 조회"""
    try:
        # 회사 정보 조회 (company_code로 조회)
        try:
            company = Company.objects.get(company_code=company_id)
        except Company.DoesNotExist:
            # 기존 id로도 시도 (하위 호환성) - 하지만 company_code가 primary_key이므로 동일한 결과
            try:
                company = Company.objects.get(pk=company_id)
            except Company.DoesNotExist:
                return Response({
                    'error': f'회사를 찾을 수 없습니다. (company_id: {company_id})'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # 여러 방법으로 SalesData 찾기
        sales_data_qs = SalesData.objects.none()
        matched_by = None
        
        # 디버깅 정보 출력
        print(f"[get_company_unique_products] 회사 정보:")
        print(f"  - company_code: {company.company_code}")
        print(f"  - company_code_sap: {company.company_code_sap}")
        print(f"  - company_name: {company.company_name}")
        
        # 방법 1: SAP 회사 코드로 매칭 (가장 정확한 방법 - 우선순위 1)
        if company.company_code_sap:
            try:
                print(f"[get_company_unique_products] 방법 1 시도: company_code_sap='{company.company_code_sap}'로 SalesData 검색")
                sales_data_qs = SalesData.objects.filter(코드=company.company_code_sap)
                count = sales_data_qs.count()
                print(f"[get_company_unique_products] 방법 1 결과: {count}개 데이터 발견")
                if count > 0:
                    matched_by = 'sap_code'
            except Exception as e:
                print(f"[get_company_unique_products] 방법 1 오류: {str(e)}")
                print(traceback.format_exc())
        
        # 방법 2: company_obj로 직접 연결된 데이터 (우선순위 2)
        if not sales_data_qs.exists():
            try:
                print(f"[get_company_unique_products] 방법 2 시도: company_obj로 SalesData 검색")
                sales_data_qs = SalesData.objects.filter(company_obj=company)
                count = sales_data_qs.count()
                print(f"[get_company_unique_products] 방법 2 결과: {count}개 데이터 발견")
                if count > 0:
                    matched_by = 'company_obj'
            except Exception as e:
                print(f"[get_company_unique_products] 방법 2 오류: {str(e)}")
                print(traceback.format_exc())
        
        # 방법 3: 회사 코드로 매칭 (우선순위 3)
        if not sales_data_qs.exists() and company.company_code:
            try:
                print(f"[get_company_unique_products] 방법 3 시도: company_code='{company.company_code}'로 SalesData 검색")
                sales_data_qs = SalesData.objects.filter(코드=company.company_code)
                count = sales_data_qs.count()
                print(f"[get_company_unique_products] 방법 3 결과: {count}개 데이터 발견")
                if count > 0:
                    matched_by = 'company_code'
            except Exception as e:
                print(f"[get_company_unique_products] 방법 3 오류: {str(e)}")
                print(traceback.format_exc())
        
        # 방법 4: 거래처명으로 매칭 (우선순위 4)
        if not sales_data_qs.exists() and company.company_name:
            try:
                print(f"[get_company_unique_products] 방법 4 시도: 거래처명='{company.company_name}'로 SalesData 검색")
                sales_data_qs = SalesData.objects.filter(거래처명__icontains=company.company_name)
                count = sales_data_qs.count()
                print(f"[get_company_unique_products] 방법 4 결과: {count}개 데이터 발견")
                if count > 0:
                    matched_by = 'company_name'
            except Exception as e:
                print(f"[get_company_unique_products] 방법 4 오류: {str(e)}")
                print(traceback.format_exc())
        
        # 유니크한 상품명 조회
        try:
            unique_products = sales_data_qs.values_list('상품명', flat=True).distinct()
            
            # None 값 제거 및 필터링
            products = [p for p in unique_products if p and p.strip()]
            
            return Response({
                'products': products,
                'count': len(products),
                'matched_by': matched_by or 'none'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"[get_company_unique_products] 상품명 조회 오류: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'error': f'상품명 조회 중 오류가 발생했습니다: {str(e)}',
                'products': [],
                'count': 0,
                'matched_by': matched_by or 'none'
            }, status=status.HTTP_200_OK)  # 에러가 발생해도 빈 배열 반환
        
    except Company.DoesNotExist:
        return Response({
            'error': f'회사를 찾을 수 없습니다. (company_id: {company_id})'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[get_company_unique_products] 전체 오류: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_sales_data(request, company_id):
    """특정 회사의 최근 12개월 SalesData 조회"""
    try:
        # 회사 정보 조회 (company_code로 조회)
        try:
            company = Company.objects.get(company_code=company_id)
        except Company.DoesNotExist:
            # 기존 id로도 시도 (하위 호환성)
            try:
                company = Company.objects.get(pk=company_id)
            except Company.DoesNotExist:
                return Response({
                    'error': '회사를 찾을 수 없습니다.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        company_code_sap = company.company_code_sap
        
        # company_code_sap가 없으면 빈 데이터 반환 (400 에러 대신)
        if not company_code_sap:
            # 최근 12개월 날짜 범위 계산
            end_date = timezone.now().date()
            current_date = timezone.now()
            all_months = []
            for i in range(12):
                month_date = current_date - timedelta(days=30*i)
                month_key = month_date.strftime('%Y-%m')
                all_months.append(month_key)
            all_months.reverse()
            
            # 빈 데이터 구조 반환
            sales_chart_data = []
            for month in all_months:
                sales_chart_data.append({
                    'month': month,
                    '매출금액': 0,
                    '매출이익': 0,
                    'GP': 0
                })
            
            return Response({
                'company_name': company.company_name,
                'company_code_sap': None,
                'sales_chart_data': sales_chart_data,
                'products_chart_data': [],
                'total_records': 0
            }, status=status.HTTP_200_OK)
        
        # 최근 12개월 날짜 범위 계산
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)  # 약 12개월
        
        # 최근 12개월의 모든 달 생성
        all_months = []
        current_date = timezone.now()
        for i in range(12):
            month_date = current_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            all_months.append(month_key)
        all_months.reverse()  # 오래된 순서로 정렬
        
        # SalesData에서 해당 회사코드와 일치하는 데이터 조회
        sales_data = SalesData.objects.filter(
            코드=company_code_sap,
            매출일자__gte=start_date,
            매출일자__lte=end_date
        ).order_by('매출일자')
        
        # 월별 매출 데이터 집계 (모든 달 초기화)
        monthly_sales = {}
        for month in all_months:
            monthly_sales[month] = {
                'month': month,
                '매출금액': 0,
                '매출이익': 0,
                'GP': 0
            }
        
        # 실제 데이터로 집계
        for data in sales_data:
            month_key = data.매출일자.strftime('%Y-%m')
            
            # 월별 매출 집계
            if month_key in monthly_sales:
                monthly_sales[month_key]['매출금액'] += data.매출금액 or 0
                monthly_sales[month_key]['매출이익'] += data.매출이익 or 0
                
                # 디버깅용 로그 (미트미 C0000020만)
                if company_code_sap == 'C0000020' and month_key == '2024-06':
                    print(f"[매출집계] {month_key}: 매출금액={data.매출금액}, 매출이익={data.매출이익}")
        
        # 월별 축종별 중량 집계 (모든 달과 축종 조합 초기화)
        monthly_products = {}
        all_products = set()
        
        # 먼저 모든 축종 수집
        for data in sales_data:
            if data.축종_부위:
                all_products.add(data.축종_부위)
        
        # 모든 달과 축종 조합 초기화
        for month in all_months:
            for product in all_products:
                product_key = f"{month}_{product}"
                monthly_products[product_key] = {
                    'month': month,
                    '축종_부위': product,
                    '중량_Kg': 0
                }
        
        # 실제 데이터로 집계
        for data in sales_data:
            month_key = data.매출일자.strftime('%Y-%m')
            if data.축종_부위 and month_key in monthly_sales:
                product_key = f"{month_key}_{data.축종_부위}"
                if product_key in monthly_products:
                    monthly_products[product_key]['중량_Kg'] += data.중량_Kg or 0
        
        # GP 계산 (매출이익/매출금액*100) - 소수점 첫째자리까지
        for month_data in monthly_sales.values():
            if month_data['매출금액'] > 0:
                gp_value = (month_data['매출이익'] / month_data['매출금액']) * 100
                # 소수점 첫째자리까지 반올림
                month_data['GP'] = round(gp_value, 1)
                print(f"[GP 계산] {month_data['month']}: 매출금액={month_data['매출금액']}, 매출이익={month_data['매출이익']}, GP={month_data['GP']}%")
            else:
                month_data['GP'] = 0  # 매출금액이 0이면 GP도 0
                print(f"[GP 계산] {month_data['month']}: 매출금액=0, GP=0%")
        
        # 축종별 데이터를 월별로 그룹화하여 차트용 데이터 생성
        # 이미 생성된 all_months와 all_products 사용
        products_chart_data = []
        for month in all_months:
            month_data = {'month': month}
            for product in all_products:
                product_key = f"{month}_{product}"
                if product_key in monthly_products:
                    month_data[product] = monthly_products[product_key]['중량_Kg']
                else:
                    month_data[product] = 0
            products_chart_data.append(month_data)
        
        # 최근 12개월 데이터 정렬
        sales_chart_data = sorted(monthly_sales.values(), key=lambda x: x['month'])
        
        return Response({
            'company_name': company.company_name,
            'company_code_sap': company_code_sap,
            'sales_chart_data': sales_chart_data,
            'products_chart_data': products_chart_data,
            'total_records': sales_data.count()
        }, status=status.HTTP_200_OK)
        
    except Company.DoesNotExist:
        return Response({
            'error': '회사를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def users_list_view(request):
    """사용자 목록을 반환하는 API"""
    try:
        users = User.objects.all().order_by('id')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'사용자 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def debug_all_fields(row_num, label, params, original_map):
    print(f"[디버깅] {row_num}행: {label}")
    for key in params:
        val = params[key]
        original_val = original_map.get(key)
        value_type = type(val).__name__ if val is not None else 'None'
        original_type = type(original_val).__name__ if original_val is not None else 'None'
        try:
            field_meta = SalesData._meta.get_field(key)
            field_class = field_meta.__class__.__name__
            db_type = field_meta.db_type(connection)
        except Exception:
            field_class = 'Unknown'
            db_type = 'Unknown'
        print(f"  - {key}: value={val!r} (type={value_type}) | original={original_val!r} (type={original_type}) | field={field_class} | db_type={db_type}")