from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime
from .models import Company, Report, User
from .serializers import CompanySerializer, ReportSerializer, UserSerializer, LoginSerializer, RegisterSerializer

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
                Q(ceo_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(address__icontains=search)
            )
        
        if customer_classification:
            queryset = queryset.filter(customer_classification=customer_classification)
            
        if industry_name:
            queryset = queryset.filter(industry_name__icontains=industry_name)
        
        return queryset.order_by('company_name')

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()  # type: ignore[attr-defined]
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'admin':
            # 관리자라면 전체 영업일지 반환
            return Report.objects.all()
        # 일반 사용자는 본인 영업일지만 반환
        return Report.objects.filter(author=user)

    def perform_create(self, serializer):
        # 현재 사용자를 author로 설정
        serializer.save(author=self.request.user, team=self.request.user.department)

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
