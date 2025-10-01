from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Max
from django.utils import timezone
from datetime import timedelta
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from .serializers import CompanySerializer, ReportSerializer, UserSerializer, LoginSerializer, RegisterSerializer, CompanyFinancialStatusSerializer, SalesDataSerializer
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
import numpy as np
from rest_framework.pagination import PageNumberPagination
from . import models
from rest_framework.generics import ListAPIView
import csv
import io
from django.http import HttpResponse
from django.utils.encoding import escape_uri_path
import pandas as pd
from decimal import Decimal
import logging
import openpyxl
from io import BytesIO

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
    print(f"[태그 임베딩 캐싱 완료] 후보 태그 수: {len(TAG_CANDIDATES)}")

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

        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(username__name__icontains=search) |
                Q(username__username__icontains=search)
            )
        if customer_classification:
            queryset = queryset.filter(customer_classification=customer_classification)
        if industry_name:
            queryset = queryset.filter(industry_name__icontains=industry_name)
        return queryset.order_by('company_name')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 연결된 영업일지(Report)가 있는지 확인
        if instance.reports.exists():
            return Response({'error': '이 회사에 연결된 영업일지가 존재하여 삭제할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST, content_type='application/json')
        return super().destroy(request, *args, **kwargs)

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()  # type: ignore[attr-defined]
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'admin':
            # 관리자라면 전체 영업일지 반환
            queryset = Report.objects.all()
        else:
            # 일반 사용자는 본인 영업일지만 반환
            queryset = Report.objects.filter(author=user)
        
        # 방문일자 기준으로 내림차순 정렬 (최신순)
        return queryset.order_by('-visitDate')

    def perform_create(self, serializer):
        # 현재 사용자를 author로 설정
        serializer.save(author=self.request.user, team=self.request.user.department)
    
    def create(self, request, *args, **kwargs):
        """영업일지 생성 시 회사 데이터 이용 로직"""
        data = request.data.copy()
        
        # 회사 관련 데이터 추출
        company_name = data.get('company', '')
        company_location = data.get('location', '')
        company_products = data.get('products', '')
        
        company_obj = None
        
        # 회사 참조가 있는 경우
        if data.get('company_obj'):
            company_obj = Company.objects.get(id=data['company_obj'])
            # 회사 데이터에서 소재지/사용품목을 가져와서 데이터에 설정
            data['location'] = company_obj.location or company_location
            data['products'] = company_obj.products or company_products
        else:
            # 기존 회사명으로 검색
            existing_company = Company.objects.filter(company_name=company_name).first()
            if existing_company:
                company_obj = existing_company
                data['company_obj'] = existing_company.id
                # 회사 데이터에서 소재지/사용품목을 가져와서 데이터에 설정
                data['location'] = existing_company.location or company_location
                data['products'] = existing_company.products or company_products
            else:
                # 신규 회사 생성
                new_company = Company.objects.create(
                    company_name=company_name,
                    sales_diary_company_code=f'C{Company.objects.count() + 1:07d}',
                    customer_classification='잠재',
                    location=company_location,
                    products=company_products,
                    username=request.user
                )
                company_obj = new_company
                data['company_obj'] = new_company.id
                # 설정된 소재지/사용품목을 데이터에 설정
                data['location'] = company_location
                data['products'] = company_products
        
        # 회사 데이터 업데이트 (사용자가 소재지/사용품목을 입력한 경우)
        if company_obj and (company_location or company_products):
            if company_location:
                company_obj.location = company_location
            if company_products:
                company_obj.products = company_products
            company_obj.save()
        
        request.data._mutable = True
        request.data.clear()
        request.data.update(data)
        request.data._mutable = False
        
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """영업일지 수정 시 회사 데이터 이용 로직"""
        instance = self.get_object()
        data = request.data.copy()
        
        # 회사 관련 데이터 추출
        company_obj = None
        if data.get('company_obj') or instance.company_obj:
            company_obj = instance.company_obj
            if data.get('company_obj'):
                try:
                    company_obj = Company.objects.get(id=data['company_obj'])
                except Company.DoesNotExist:
                    pass
        
        # 회사 데이터가 있으면 해당 데이터로 설정 (사용자가 입력하지 않았을 때만)
        if company_obj and not data.get('location') and not instance.location:
            data['location'] = company_obj.location
        if company_obj and not data.get('products') and not instance.products:
            data['products'] = company_obj.products
        
        request.data._mutable = True
        request.data.clear()
        request.data.update(data)
        request.data._mutable = False
        
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # 업데이트 시에도 author와 team은 변경하지 않음
        serializer.save()

    def update_with_error_handling(self, request, *args, **kwargs):
        """영업일지 수정 시 더 자세한 오류 처리"""
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"영업일지 수정 오류: {e}")
            print(f"요청 데이터: {request.data}")
            return Response({
                'error': '영업일지 수정 중 오류가 발생했습니다.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        id = serializer.validated_data['id']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=id, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'message': '로그인 성공',
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'department': user.department,
                    'employee_number': user.employee_number,
                    'role': user.role
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

@api_view(['GET'])
@permission_classes([AllowAny])
def company_stats_view(request):
    """회사 통계 정보를 반환하는 API"""
    try:
        # 현재 날짜 정보
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        
        # 전체 회사 수
        total_companies = Company.objects.count()
        
        # 신규 고객사 수 (customer_classification이 '신규'인 경우)
        new_customers = Company.objects.filter(
            customer_classification='신규'
        ).count()
        
        # 기존 고객사 수 (customer_classification이 '기존'인 경우)
        existing_customers = Company.objects.filter(
            customer_classification='기존'
        ).count()
        
        # 이번 달 신규 고객사 수
        # transaction_start_date가 이번 달이고 customer_classification이 '신규'인 경우
        this_month_new = Company.objects.filter(
            transaction_start_date__year=current_year,
            transaction_start_date__month=current_month,
            customer_classification='신규'
        ).count()
        
        return Response({
            'total': total_companies,
            'newCustomers': new_customers,
            'existingCustomers': existing_customers,
            'thisMonthNew': this_month_new
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
            companies_queryset = Company.objects.filter(username=user)
        
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
            
            # 사용자별 필터링
            if not (hasattr(user, 'role') and user.role == 'admin'):
                this_month_sales = this_month_sales.filter(
                    Q(매출담당자__icontains=user.name) |
                    Q(담당자__icontains=user.name)
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
            companies_queryset = Company.objects.filter(username=user)
        
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
            
            # 사용자별 필터링 (관리자가 아닌 경우)
            if not (hasattr(user, 'role') and user.role == 'admin'):
                monthly_sales_queryset = monthly_sales_queryset.filter(
                    Q(매출담당자__icontains=user.name) |
                    Q(담당자__icontains=user.name)
                )
            
            # 월별 매출 합계 계산
            monthly_revenue = sum(sales.매출금액 for sales in monthly_sales_queryset)
            monthly_quantity = sum(sales.Box or 0 for sales in monthly_sales_queryset)
            monthly_transactions = monthly_sales_queryset.count()
            
            # 디버깅: 6월 데이터 특별 출력
            if target_month == 6:
                print(f"=== 6월 매출 데이터 디버깅 ({target_year}년) ===")
                print(f"사용자: {user.name if user else 'No user'}")
                print(f"사용자 role: {getattr(user, 'role', 'No role') if user else 'No user'}")
                print(f"관리자 여부: {hasattr(user, 'role') and user.role == 'admin' if user else 'No user'}")
                print(f"필터링 전 총 데이터: {SalesData.objects.filter(매출일자__year=target_year, 매출일자__month=target_month).count()}건")
                print(f"필터링 후 데이터: {monthly_transactions}건")
                print(f"6월 매출합계: {monthly_revenue:,}원")
                print(f"6월 Box 누적: {monthly_quantity:,}개")
            
            # 매출이 0이면 영업일지 수 기반으로 추정
            if monthly_revenue == 0:
                try:
                    monthly_reports = reports_queryset.filter(
                        visitDate__year=target_year,
                        visitDate__month=target_month
                    ).count()
                except Exception as e:
                    monthly_reports = 0
                
                # 영업일지 1건당 평균 가정 매출
                monthly_revenue = monthly_reports * 50000000  # 5천만원 가정
                monthly_transactions = monthly_reports
            
            sales_data.append({
                'name': month_name,
                '매출액': monthly_revenue,
                '매출수량': monthly_quantity or (monthly_transactions * 50),  # 월련량 또는 추정량
                '매출건수': monthly_transactions
            })
        
        # 시간순으로 정렬 (최근 6개월 전부터 현재까지)
        sales_data = list(reversed(sales_data))
        
        # 채널별 매출 비율 데이터 생성 (유통유형 기반)
        channel_types = ['가공장', '프랜차이즈', '도소매']
        channel_data = []
        
        try:
            for i, channel_type in enumerate(channel_types):
                channel_companies = companies_queryset.filter(
                    distribution_type_sap__icontains=channel_type
                ).count()
                
                # 전체 회사 대비 비율 계산
                total_companies_count = companies_queryset.count()
                if total_companies_count > 0:
                    percentage = round((channel_companies / total_companies_count) * 100)
                else:
                    percentage = 0
                
                colors = ["#0088FE", "#00C49F", "#FFBB28"]
                channel_data.append({
                    'name': channel_type,
                    'value': percentage if percentage > 0 else 25,  # 최소값 보장
                    'color': colors[i]
                })
        except Exception as e:
            # 오류 발생 시 기본값 설정
            channel_data = [
                {'name': '가공장', 'value': 45, 'color': '#0088FE'},
                {'name': '프랜차이즈', 'value': 30, 'color': '#00C49F'},
                {'name': '도소매', 'value': 25, 'color': '#FFBB28'}
            ]
        
        # 최근 영업 활동 데이터
        recent_activities = []
        try:
            recent_reports = reports_queryset.order_by('-visitDate')[:4]
            
            for report in recent_reports:
                recent_activities.append({
                    'company': report.company,
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
    """회사명 자동완성을 위한 API"""
    try:
        query = request.GET.get('query', '').strip()
        
        if not query or len(query) < 1:
            return Response([], status=status.HTTP_200_OK)
        
        # 회사명으로 LIKE 검색 (대소문자 구분 없음)
        companies = Company.objects.filter(
            company_name__icontains=query
        ).values('id', 'company_name')[:10]  # 최대 10개
        
        # 응답 형식: [{"id": 1, "name": "삼성식자재"}, {"id": 2, "name": "삼성유통"}]
        suggestions = [
            {"id": company['id'], "name": company['company_name']}
            for company in companies
        ]
        
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
    - 회사명이 DB에 없으면 'C'+7자리 순차 ID, 고객분류 '잠재'로 생성
    - 이미 있으면 중복 등록하지 않고 기존 회사 반환
    """
    name = request.data.get('company_name')
    if not name:
        return Response({'error': '회사명이 필요합니다.'}, status=400)
    # 중복 체크 (회사명 완전일치)
    company = Company.objects.filter(company_name=name).first()
    if company:
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=200)
    # 회사ID 생성: sales_diary_company_code = 'C'+7자리
    last_code = Company.objects.filter(sales_diary_company_code__startswith='C').aggregate(
        max_code=Max('sales_diary_company_code')
    )['max_code']
    if last_code and last_code[1:].isdigit():
        next_num = int(last_code[1:]) + 1
    else:
        next_num = 1
    new_code = f'C{next_num:07d}'
    company = Company.objects.create(
        company_name=name,
        sales_diary_company_code=new_code,
        customer_classification='잠재'
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
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': '텍스트가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        # 태그 후보 및 임베딩 캐싱 (최초 1회만)
        global TAG_CANDIDATES, TAG_EMBEDDINGS, TAG_MODEL
        if TAG_CANDIDATES is None or TAG_EMBEDDINGS is None or TAG_MODEL is None:
            load_tag_candidates_and_embeddings()
        # 1. 입력 문장에 실제로 등장하는 DB 태그 우선 추출
        direct_tags = [tag for tag in TAG_CANDIDATES if tag and tag in text]
        # 2. KeyBERT로 후보 추출
        kw_model = KeyBERT(model=TAG_MODEL)
        keybert_keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words=None,
            top_n=10  # 기존 20 → 10으로 속도 개선
        )
        candidates = [kw[0] if not isinstance(kw[0], tuple) else ' '.join(kw[0]) for kw in keybert_keywords]
        candidate_embeddings = TAG_MODEL.encode(candidates, convert_to_tensor=True)
        matched_tags = set(direct_tags)
        for i, cand_emb in enumerate(candidate_embeddings):
            cos_scores = util.pytorch_cos_sim(cand_emb, TAG_EMBEDDINGS)[0]
            best_idx = int(np.argmax(cos_scores))
            best_score = float(cos_scores[best_idx])
            candidate = candidates[i]
            db_tag = TAG_CANDIDATES[best_idx]
            if db_tag in text:
                matched_tags.add(db_tag)
            elif best_score >= 0.75:
                matched_tags.add(db_tag)
        # 최대 10개 반환
        return Response({
            'keywords': list(matched_tags)[:10]
        }, status=status.HTTP_200_OK)
    except Exception as e:
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
        user = self.request.user
        queryset = Report.objects.all()
        # 인증 및 권한 분기
        if user and user.is_authenticated and hasattr(user, 'role'):
            if user.role != 'admin':
                queryset = queryset.filter(author=user)
        # 검색/필터/정렬
        search = self.request.query_params.get('search', '').strip()
        period = self.request.query_params.get('period', 'all')
        ordering = self.request.query_params.get('ordering', '-visitDate')
        company_id = self.request.query_params.get('companyId', '').strip()

        if company_id:
            queryset = queryset.filter(
                Q(company_obj__sales_diary_company_code=company_id) |
                Q(company=company_id)
            )
        if search:
            queryset = queryset.filter(
                Q(company__icontains=search) |
                Q(author__username__icontains=search) |
                Q(author__name__icontains=search) |
                Q(tags__icontains=search)
            )
        if period in ['1m', '3m', '6m']:
            months = int(period[0])
            start_date = timezone.now().date() - timedelta(days=30 * months)
            queryset = queryset.filter(visitDate__gte=start_date)
        queryset = queryset.order_by(ordering)
        return queryset

class CompanyFinancialStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.CompanyFinancialStatus.objects.all()
    serializer_class = CompanyFinancialStatusSerializer
    permission_classes = [IsAuthenticated]

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
            queryset = SalesData.objects.filter(
                Q(매출담당자__icontains=user.name) |
                Q(담당자__icontains=user.name) |
                Q(company_obj__username=user)
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
        reports = Report.objects.select_related('author', 'company_obj').all()
        
        # CSV 응답 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path("영업일지_백업.csv")}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        writer = csv.writer(response)
        
        # 헤더 작성
        writer.writerow([
            'ID', '작성자ID', '작성자명', '팀명', '방문일자', '회사명', '회사ID', '영업형태',
            '소재지', '사용품목', '미팅내용', '태그', '작성일'
        ])
        
        # 데이터 작성
        for report in reports:
            writer.writerow([
                report.id,
                report.author.id if report.author else '',
                report.author.name if report.author else '',
                report.team,
                report.visitDate.strftime('%Y-%m-%d') if report.visitDate else '',
                report.company,
                report.company_obj.id if report.company_obj else '',
                report.type,
                report.location or '',  # 소재지 필드 추가
                report.products or '',  # 사용품목 필드 추가
                report.content,
                report.tags,
                report.createdAt.strftime('%Y-%m-%d %H:%M:%S') if report.createdAt else ''
            ])
        
        return response
        
    except Exception as e:
        logging.error(f'영업일지 CSV 다운로드 오류: {e}')
        return Response({'error': '다운로드 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_companies_csv(request):
    """회사 데이터를 CSV로 다운로드"""
    try:
        # 관리자 권한 확인
        if not hasattr(request.user, 'role') or request.user.role != 'admin':
            return Response({'error': '관리자만 다운로드할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        
        # 모든 회사 데이터 조회
        companies = Company.objects.select_related('username').all()
        
        # CSV 응답 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="{escape_uri_path("회사_백업.csv")}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        writer = csv.writer(response)
        
        # 헤더 작성
        writer.writerow([
            'ID', '회사명', '영업일지회사코드', 'SM회사코드', 'SAP회사코드', '회사유형', '설립일', 
            '대표자명', '주소', '담당자', '담당자연락처', '대표전화', 'SAP유통유형', '업종명', 
            '주요제품', '거래시작일', '결제조건', '고객분류', '웹사이트', '비고', '영업사원ID', 
            '영업사원명', '소재지', '사용품목'
        ])
        
        # 데이터 작성
        for company in companies:
            writer.writerow([
                company.id,
                company.company_name or '',
                company.sales_diary_company_code or '',
                company.company_code_sm or '',
                company.company_code_sap or '',
                company.company_type or '',
                company.established_date.strftime('%Y-%m-%d') if company.established_date else '',
                company.ceo_name or '',
                company.address or '',
                company.contact_person or '',
                company.contact_phone or '',
                company.main_phone or '',
                company.distribution_type_sap or '',
                company.industry_name or '',
                company.main_product or '',
                company.transaction_start_date.strftime('%Y-%m-%d') if company.transaction_start_date else '',
                company.payment_terms or '',
                company.customer_classification or '',
                company.website or '',
                company.remarks or '',
                company.username.id if company.username else '',
                company.username.name if company.username else '',
                company.location or '',  # 새로 추가된 필드
                company.products or ''    # 새로 추가된 필드
            ])
        
        return response
        
    except Exception as e:
        logging.error(f'회사 CSV 다운로드 오류: {e}')
        return Response({'error': '다운로드 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_reports_csv(request):
    """영업일지 CSV 파일을 업로드하여 일괄 업데이트/생성"""
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
        
        # 필요한 컬럼 확인
        required_columns = ['ID', '작성자ID', '작성자명', '팀명', '방문일자', '회사명', '회사ID', '영업형태', '소재지', '사용품목', '미팅내용', '태그', '작성일']
        if not all(col in df.columns for col in required_columns):
            return Response({'error': '파일에 필요한 컬럼이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = 0
        created_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                report_id = int(row['ID']) if pd.notna(row['ID']) else None
                author_id = int(row['작성자ID']) if pd.notna(row['작성자ID']) else None
                company_id = int(row['회사ID']) if pd.notna(row['회사ID']) else None
                
                # 작성자 확인
                author = None
                if author_id:
                    try:
                        author = User.objects.get(id=author_id)
                    except User.DoesNotExist:
                        errors.append(f"행 {index + 2}: 작성자가 존재하지 않습니다 (ID: {author_id})")
                        continue
                
                # 회사 확인
                company_obj = None
                if company_id:
                    try:
                        company_obj = Company.objects.get(id=company_id)
                    except Company.DoesNotExist:
                        errors.append(f"행 {index + 2}: 회사가 존재하지 않습니다 (ID: {company_id})")
                        continue
                
                # 날짜 변환
                visit_date = None
                if pd.notna(row['방문일자']):
                    try:
                        visit_date = pd.to_datetime(row['방문일자']).date()
                    except:
                        errors.append(f"행 {index + 2}: 방문일자 형식이 올바르지 않습니다")
                        continue
                
                # 기존 영업일지 업데이트 또는 새로 생성
                if report_id and Report.objects.filter(id=report_id).exists():
                    report = Report.objects.get(id=report_id)
                    report.author = author
                    report.team = row['팀명'] if pd.notna(row['팀명']) else ''
                    report.visitDate = visit_date
                    report.company = row['회사명'] if pd.notna(row['회사명']) else ''
                    report.company_obj = company_obj
                    report.type = row['영업형태'] if pd.notna(row['영업형태']) else ''
                    report.location = row['소재지'] if pd.notna(row['소재지']) else ''
                    report.products = row['사용품목'] if pd.notna(row['사용품목']) else ''
                    report.content = row['미팅내용'] if pd.notna(row['미팅내용']) else ''
                    report.tags = row['태그'] if pd.notna(row['태그']) else ''
                    report.save()
                    updated_count += 1
                else:
                    Report.objects.create(
                        author=author,
                        team=row['팀명'] if pd.notna(row['팀명']) else '',
                        visitDate=visit_date,
                        company=row['회사명'] if pd.notna(row['회사명']) else '',
                        company_obj=company_obj,
                        type=row['영업형태'] if pd.notna(row['영업형태']) else '',
                        location=row['소재지'] if pd.notna(row['소재지']) else '',
                        products=row['사용품목'] if pd.notna(row['사용품목']) else '',
                        content=row['미팅내용'] if pd.notna(row['미팅내용']) else '',
                        tags=row['태그'] if pd.notna(row['태그']) else ''
                    )
                    created_count += 1
                    
            except Exception as e:
                errors.append(f"행 {index + 2}: {str(e)}")
                continue
        
        return Response({
            'message': f'영업일지 업로드 완료: {created_count}개 생성, {updated_count}개 업데이트',
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors[:10]  # 최대 10개 오류만 반환
        })
        
    except Exception as e:
        logging.error(f'영업일지 CSV 업로드 오류: {e}')
        return Response({'error': '업로드 중 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        
        # 필요한 컬럼 확인
        required_columns = ['ID', '회사명', '영업일지회사코드', '영업사원ID', '소재지', '사용품목']
        if not all(col in df.columns for col in required_columns):
            return Response({'error': '파일에 필요한 컬럼이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = 0
        created_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                company_id = int(row['ID']) if pd.notna(row['ID']) else None
                sales_person_id = int(row['영업사원ID']) if pd.notna(row['영업사원ID']) else None
                
                # 영업사원 확인
                sales_person = None
                if sales_person_id:
                    try:
                        sales_person = User.objects.get(id=sales_person_id)
                    except User.DoesNotExist:
                        errors.append(f"행 {index + 2}: 영업사원이 존재하지 않습니다 (ID: {sales_person_id})")
                        continue
                
                # 기존 회사 업데이트 또는 새로 생성
                if company_id and Company.objects.filter(id=company_id).exists():
                    company = Company.objects.get(id=company_id)
                    company.company_name = row['회사명'] if pd.notna(row['회사명']) else ''
                    company.sales_diary_company_code = row['영업일지회사코드'] if pd.notna(row['영업일지회사코드']) else ''
                    company.username = sales_person
                    company.location = row['소재지'] if pd.notna(row['소재지']) else ''
                    company.products = row['사용품목'] if pd.notna(row['사용품목']) else ''
                    
                    # 추가 필드들도 업데이트 (있는 경우에만)
                    if 'SM회사코드' in df.columns:
                        company.company_code_sm = row['SM회사코드'] if pd.notna(row['SM회사코드']) else ''
                    if 'SAP회사코드' in df.columns:
                        company.company_code_sap = row['SAP회사코드'] if pd.notna(row['SAP회사코드']) else ''
                    if '회사유형' in df.columns:
                        company.company_type = row['회사유형'] if pd.notna(row['회사유형']) else ''
                    if '설립일' in df.columns and pd.notna(row['설립일']):
                        try:
                            company.established_date = pd.to_datetime(row['설립일']).date()
                        except:
                            pass
                    if '대표자명' in df.columns:
                        company.ceo_name = row['대표자명'] if pd.notna(row['대표자명']) else ''
                    if '주소' in df.columns:
                        company.address = row['주소'] if pd.notna(row['주소']) else ''
                    if '담당자' in df.columns:
                        company.contact_person = row['담당자'] if pd.notna(row['담당자']) else ''
                    if '담당자연락처' in df.columns:
                        company.contact_phone = row['담당자연락처'] if pd.notna(row['담당자연락처']) else ''
                    if '대표전화' in df.columns:
                        company.main_phone = row['대표전화'] if pd.notna(row['대표전화']) else ''
                    if '업종명' in df.columns:
                        company.industry_name = row['업종명'] if pd.notna(row['업종명']) else ''
                    if '주요제품' in df.columns:
                        company.main_product = row['주요제품'] if pd.notna(row['주요제품']) else ''
                    if '고객분류' in df.columns:
                        company.customer_classification = row['고객분류'] if pd.notna(row['고객분류']) else ''
                    if '비고' in df.columns:
                        company.remarks = row['비고'] if pd.notna(row['비고']) else ''
                    
                    company.save()
                    updated_count += 1
                else:
                    Company.objects.create(
                        company_name=row['회사명'] if pd.notna(row['회사명']) else '',
                        sales_diary_company_code=row['영업일지회사코드'] if pd.notna(row['영업일지회사코드']) else '',
                        username=sales_person,
                        location=row['소재지'] if pd.notna(row['소재지']) else '',
                        products=row['사용품목'] if pd.notna(row['사용품목']) else '',
                        company_type=row['회사유형'] if pd.notna(row['회사유형']) and '회사유형' in df.columns else '',
                        industry_name=row['업종명'] if pd.notna(row['업종명']) and '업종명' in df.columns else '',
                        customer_classification=row['고객분류'] if pd.notna(row['고객분류']) and '고객분류' in df.columns else '잠재'
                    )
                    created_count += 1
                    
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
        if file_extension not in ['csv', 'xlsx']:
            return Response({'error': 'CSV 또는 XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 읽기 (CSV 또는 XLSX)
        if file_extension == 'csv':
            csv_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(csv_data.splitlines())
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
        
        for row_num, row in enumerate(csv_reader, start=2):  # 헤더가 1행이므로 2부터 시작
            try:
                # 거래처명이 없는 경우 건너뛰기
                if not row.get('거래처명', '').strip():
                    continue
                
                # 필수 필드 검증
                if not row.get('매출일자', '').strip():
                    errors.append(f"{row_num}행: 매출일자가 필요합니다.")
                    continue
                
                if not row.get('매출금액', '').strip():
                    errors.append(f"{row_num}행: 매출금액이 필요합니다.")
                    continue
                
                # 매출일자 파싱
                try:
                    매출일자 = pd.to_datetime(row['매출일자']).date()
                except:
                    errors.append(f"{row_num}행: 매출일자 형식이 올바르지 않습니다.")
                    continue
                
                # 매출금액 파싱 (쉼표 제거 후 정수로 변환)
                try:
                    매출금액_str = str(row['매출금액']).replace(',', '').replace(' ', '')
                    매출금액 = int(float(매출금액_str)) if 매출금액_str else 0
                except:
                    errors.append(f"{row_num}행: 매출금액 형식이 올바르지 않습니다.")
                    continue
                
                # 회사 연결 시도
                company_obj = None
                거래처명 = row['거래처명'].strip()
                try:
                    # 거래처명으로 회사 찾기
                    company_obj = Company.objects.filter(
                        Q(company_name__icontains=거래처명) |
                        Q(sales_diary_company_code__contains=거래처명)
                    ).first()
                except:
                    pass
                
                # Box 파싱 (있는 경우만)
                Box = None
                if row.get('Box', '').strip():
                    try:
                        Box = int(row['Box'])
                    except:
                        pass
                
                # 중량 파싱 (있는 경우만)
                중량_Kg = None
                if row.get('중량(Kg)', '').strip():
                    try:
                        중량_Kg = float(row['중량(Kg)'])
                    except:
                        pass
                
                # 기타 필드들도 비슷하게 파싱...
                sales_data, created = SalesData.objects.get_or_create(
                    매출일자=매출일자,
                    거래처명=거래처명,
                    매출금액=매출금액,
                    defaults={
                        '코드': row.get('코드', '').strip() or None,
                        '매출부서': row.get('매출부서', '').strip() or None,
                        '매출담당자': row.get('매출담당자', '').strip() or None,
                        '유통형태': row.get('유통형태', '').strip() or None,
                        '상품코드': row.get('상품코드', '').strip() or None,
                        '상품명': row.get('상품명', '').strip() or None,
                        '브랜드': row.get('브랜드', '').strip() or None,
                        '축종': row.get('축종', '').strip() or None,
                        '부위': row.get('부위', '').strip() or None,
                        '원산지': row.get('원산지', '').strip() or None,
                        '축종_부위': row.get('축종-부위', '').strip() or None,
                        '원산지_축종': row.get('원산지', '').strip() or None,
                        '등급': row.get('등급', '').strip() or None,
                        'Box': Box,
                        '중량_Kg': 중량_Kg,
                        '매출단가': None,  # 필요시 별도 파싱
                        '매출이익': None,  # 필요시 별도 파싱
                        '이익율': None,    # 필요시 별도 파싱
                        '매입처': row.get('매입 처', '').strip() or None,
                        '매입일자': None,   # 필요시 별도 파싱
                        '재고보유일': None, # 필요시 별도 파싱
                        '수입로컬': row.get('수입/로컬', '').strip() or None,
                        '이관재고여부': row.get('이관재고 여부', '').strip() or None,
                        '담당자': row.get('담당자', '').strip() or None,
                        '매입단가': None,   # 필요시 별도 파싱
                        '매입금액': None,  # 필요시 별도 파싱
                        '지점명': row.get('지점명', '').strip() or None,
                        '매출비고': row.get('매출비고', '').strip() or None,
                        '매입비고': row.get('매입비고', '').strip() or None,
                        '이력번호': row.get('이력번호', '').strip() or None,
                        'BL번호': row.get('B/L번호(도체번호)', '').strip() or None,
                        'company_obj': company_obj,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            except Exception as e:
                errors.append(f"{row_num}행: {str(e)}")
                continue
        
        return Response({
            'message': f'매출 데이터 업로드 완료. 신규 생성: {created_count}건, 업데이트: {updated_count}건',
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors[:50]  # 오류 최대 50개만 반환
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'CSV 업로드 중 오류가 발생했습니다: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
