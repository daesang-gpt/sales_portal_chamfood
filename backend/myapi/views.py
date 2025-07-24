from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count, Max
from django.utils import timezone
from datetime import datetime
from .models import Company, Report, User
from .serializers import CompanySerializer, ReportSerializer, UserSerializer, LoginSerializer, RegisterSerializer
import re
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
import numpy as np

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
            queryset = Report.objects.all()
        else:
            # 일반 사용자는 본인 영업일지만 반환
            queryset = Report.objects.filter(author=user)
        
        # 방문일자 기준으로 내림차순 정렬 (최신순)
        return queryset.order_by('-visitDate')

    def perform_create(self, serializer):
        # 현재 사용자를 author로 설정
        serializer.save(author=self.request.user, team=self.request.user.department)

    def perform_update(self, serializer):
        # 업데이트 시에도 author와 team은 변경하지 않음
        serializer.save()

    def update(self, request, *args, **kwargs):
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
            top_n=20
        )
        candidates = [kw[0] if not isinstance(kw[0], tuple) else ' '.join(kw[0]) for kw in keybert_keywords]
        candidate_embeddings = TAG_MODEL.encode(candidates, convert_to_tensor=True)
        matched_tags = set(direct_tags)
        for i, cand_emb in enumerate(candidate_embeddings):
            cos_scores = util.pytorch_cos_sim(cand_emb, TAG_EMBEDDINGS)[0]
            best_idx = int(np.argmax(cos_scores))
            best_score = float(cos_scores[best_idx])
            if best_score >= 0.5:
                matched_tags.add(TAG_CANDIDATES[best_idx])
        # 최대 10개 반환
        return Response({
            'keywords': list(matched_tags)[:10]
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': '키워드 추출 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
