from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Max, Sum, Value
from django.db.models.functions import Replace
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from .serializers import CompanySerializer, ReportSerializer, UserSerializer, LoginSerializer, RegisterSerializer, CompanyFinancialStatusSerializer, SalesDataSerializer, ForgotPasswordSerializer, ChangePasswordSerializer
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
from django.core.mail import send_mail
from django.conf import settings
import secrets
import traceback
import string

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
                Q(employee_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(company_code__icontains=search) |
                Q(company_code_sap__icontains=search)
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

    def dispatch(self, request, *args, **kwargs):
        """요청이 들어오는지 확인하기 위한 dispatch 오버라이드"""
        print(f"\n[ReportViewSet.dispatch] 요청 도달: {request.method} {request.path}")
        print(f"[ReportViewSet.dispatch] action: {kwargs.get('action', 'unknown')}")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # 모든 사용자(관리자, 일반 사용자)가 전체 영업일지를 볼 수 있도록 수정
        queryset = Report.objects.all()
        
        # 방문일자 기준으로 내림차순 정렬 (최신순)
        return queryset.order_by('-visitDate')

    def perform_create(self, serializer):
        # 현재 사용자를 author로 설정하고 작성자명, 팀명 저장
        user = self.request.user
        company_obj = serializer.validated_data.get('company_obj')
        
        print("=" * 80)
        print("[perform_create] 시작")
        print(f"[perform_create] user: {user} (id: {user.id}, type: {type(user.id)})")
        print(f"[perform_create] company_obj: {company_obj} (type: {type(company_obj)})")
        if company_obj:
            print(f"[perform_create] company_obj.company_code: {company_obj.company_code} (type: {type(company_obj.company_code)})")
            print(f"[perform_create] company_obj.pk: {company_obj.pk} (type: {type(company_obj.pk)})")
        
        # Oracle 호환성을 위해 author는 ID로 명시적으로 전달
        save_kwargs = {
            'author_id': user.id,  # ForeignKey 필드에 ID 직접 전달
            'author_name': user.name if user.name else None,
            'author_department': user.department if user.department else None,
        }
        
        # 회사 정보 저장
        if company_obj:
            save_kwargs['company_name'] = company_obj.company_name or None
            save_kwargs['company_city_district'] = company_obj.city_district or None
            # Oracle에서 문자열 PK ForeignKey 처리
            # company_obj는 일반 ForeignKey이므로 company_obj_id로 문자열 PK 전달
            save_kwargs['company_obj_id'] = company_obj.company_code
            
            # company_code는 to_field='company_code'로 설정된 ForeignKey
            # save_kwargs에 문자열 값으로 직접 전달 (validated_data를 수정하는 것보다 이게 더 확실함)
            save_kwargs['company_code'] = company_obj.company_code
            print(f"[perform_create] company_code를 save_kwargs에 문자열로 추가: {company_obj.company_code} (타입: {type(company_obj.company_code)})")
            
            # validated_data에서 Company 객체 제거 (save_kwargs가 우선순위가 높으므로)
            if 'company_code' in serializer.validated_data:
                old_value = serializer.validated_data.pop('company_code')
                print(f"[perform_create] validated_data에서 company_code 제거됨 (기존 값: {old_value}, 타입: {type(old_value)})")
            
            # company_obj도 제거 (company_obj_id로 대체)
            if 'company_obj' in serializer.validated_data:
                old_company_obj = serializer.validated_data.pop('company_obj')
                print(f"[perform_create] validated_data에서 company_obj 제거됨 (company_obj_id로 대체)")
        else:
            # company_obj가 None인 경우 명시적으로 설정
            save_kwargs['company_obj_id'] = None
            save_kwargs['company_code'] = None
            if 'company_code' in serializer.validated_data:
                serializer.validated_data.pop('company_code')
            if 'company_obj' in serializer.validated_data:
                serializer.validated_data.pop('company_obj')
        
        # 상세 디버깅: 모든 필드의 값과 타입 출력
        print("\n[perform_create] save_kwargs 상세:")
        for key, value in save_kwargs.items():
            value_type = type(value)
            value_repr = repr(value)
            if hasattr(value, '__class__'):
                value_class_name = value.__class__.__name__
            else:
                value_class_name = str(value_type)
            
            # 값이 너무 길면 잘라서 표시
            if isinstance(value, str) and len(value) > 100:
                value_repr = value[:100] + "..."
            
            print(f"  {key}:")
            print(f"    값: {value_repr}")
            print(f"    타입: {value_type} ({value_class_name})")
            if hasattr(value, 'pk'):
                print(f"    pk: {value.pk} (type: {type(value.pk)})")
            if hasattr(value, 'id'):
                print(f"    id: {value.id} (type: {type(value.id)})")
        
        print(f"\n[perform_create] validated_data keys: {list(serializer.validated_data.keys())}")
        print(f"[perform_create] validated_data 상세:")
        for key, value in serializer.validated_data.items():
            print(f"  {key}: {value} (type: {type(value)})")
        
        print("\n[perform_create] serializer.instance:", serializer.instance)
        print("=" * 80)
        
        try:
            print("[perform_create] serializer.save() 호출 시작...")
            result = serializer.save(**save_kwargs)
            print(f"[perform_create] serializer.save() 성공! result: {result}")
            print(f"[perform_create] result.id: {getattr(result, 'id', 'N/A')}")
            print("=" * 80)
            return result
        except Exception as save_error:
            print("\n" + "=" * 80)
            print("[perform_create] 저장 중 오류 발생!")
            print(f"오류 타입: {type(save_error).__name__}")
            print(f"오류 메시지: {str(save_error)}")
            print("\n상세 스택 트레이스:")
            import traceback
            traceback.print_exc()
            print("=" * 80)
            raise
    
    def create(self, request, *args, **kwargs):
        """영업일지 생성 시 회사 데이터 이용 로직"""
        # 즉시 로그 출력 (요청이 도달했는지 확인)
        print("\n" + "=" * 80)
        print("=" * 80)
        print("[ReportViewSet.create] 메서드 호출됨!")
        print("=" * 80)
        print(f"[ReportViewSet.create] request.method: {request.method}")
        print(f"[ReportViewSet.create] request.path: {request.path}")
        print(f"[ReportViewSet.create] request.user: {request.user}")
        print(f"[ReportViewSet.create] request.data type: {type(request.data)}")
        print(f"[ReportViewSet.create] request.data: {request.data}")
        print("=" * 80)
        
        try:
            data = dict(request.data)
            print(f"[ReportViewSet.create] data 변환 완료: {list(data.keys())}")
            
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
            company_name_input = data.get('company_name', '')  # 회사명 입력 (선택사항, 신규 회사 생성 시 사용)
            
            company_obj = None
            
            # 회사 참조가 있는 경우 (Company PK는 company_code 문자열)
            if data.get('company_obj'):
                try:
                    company_code = data['company_obj']
                    # 문자열로 변환 (Oracle 호환성)
                    if not isinstance(company_code, str):
                        company_code = str(company_code)
                    company_obj = Company.objects.get(company_code=company_code)
                    # 회사 데이터에서 사용품목을 가져와서 데이터에 설정
                    data['products'] = company_obj.products or company_products
                except Company.DoesNotExist:
                    print(f"회사를 찾을 수 없습니다: company_code={data['company_obj']}")
                    return Response({'error': '선택하신 회사를 찾을 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            elif company_name_input:
                # 기존 회사명으로 검색
                existing_company = Company.objects.filter(company_name=company_name_input).first()
                if existing_company:
                    company_obj = existing_company
                    data['company_obj'] = existing_company.company_code
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
                    new_company = Company.objects.create(
                        company_code=new_code,
                        company_name=company_name_input,
                        customer_classification='신규',
                        products=company_products,
                        employee_name=request.user.name if request.user else None
                    )
                    company_obj = new_company
                    data['company_obj'] = new_company.company_code
                    data['products'] = company_products
            
            # 회사 데이터 업데이트 (사용자가 사용품목을 입력한 경우)
            if company_obj and company_products:
                company_obj.products = company_products
                company_obj.save()
            
            # 회사 정보를 데이터에 추가 (저장용)
            if company_obj:
                data['company_name'] = company_obj.company_name
                data['company_city_district'] = company_obj.city_district
            
            # read_only 필드 제거 (perform_create에서 설정됨)
            data.pop('author', None)
            data.pop('author_name', None)
            data.pop('author_department', None)
            data.pop('team', None)
            data.pop('location', None)  # location은 Report 모델에 없음
            
            # 빈 문자열을 None으로 변환 (Oracle 호환성)
            for key in ['sales_stage', 'products', 'tags', 'company_city_district']:
                if key in data and data[key] == '':
                    data[key] = None
            
            # 상세 디버깅: 데이터 출력
            print("\n" + "=" * 80)
            print("[create] 최종 데이터 처리")
            print("=" * 80)
            print(f"[create] data dictionary keys: {list(data.keys())}")
            print("\n[create] data 상세:")
            for key, value in data.items():
                value_type = type(value)
                if isinstance(value, str) and len(value) > 100:
                    value_repr = value[:100] + "..."
                else:
                    value_repr = repr(value)
                print(f"  {key}: {value_repr} (type: {value_type})")
            
            print(f"\n[create] company_obj: {company_obj} (type: {type(company_obj)})")
            if company_obj:
                print(f"[create] company_obj.company_code: {company_obj.company_code} (type: {type(company_obj.company_code)})")
                print(f"[create] company_obj.pk: {company_obj.pk} (type: {type(company_obj.pk)})")
            
            print(f"[create] request.user: {request.user} (id: {request.user.id}, type: {type(request.user.id)})")
            print("=" * 80 + "\n")
            
            # serializer를 직접 생성하여 처리
            print("[create] Serializer 생성 및 검증 시작...")
            serializer = self.get_serializer(data=data)
            print("[create] Serializer.is_valid() 호출...")
            serializer.is_valid(raise_exception=True)
            print("[create] Serializer 검증 완료!")
            print(f"[create] validated_data: {serializer.validated_data}")
            print("[create] perform_create 호출...")
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            print("\n" + "=" * 80)
            print("[ReportViewSet.create] 예외 발생!")
            print("=" * 80)
            print(f"[ReportViewSet.create] 예외 타입: {type(e).__name__}")
            print(f"[ReportViewSet.create] 예외 메시지: {str(e)}")
            print("\n[ReportViewSet.create] 상세 스택 트레이스:")
            import traceback
            traceback.print_exc()
            print("=" * 80 + "\n")
            return Response({'error': f'영업일지 생성 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                    # company_obj가 company_code인지 id인지 확인
                    company_code_or_id = data['company_obj']
                    try:
                        company_obj = Company.objects.get(company_code=company_code_or_id)
                    except Company.DoesNotExist:
                        try:
                            company_obj = Company.objects.get(id=company_code_or_id)
                        except Company.DoesNotExist:
                            pass
                except:
                    pass
        
        # 회사 정보 업데이트 (저장용)
        if company_obj:
            data['company_name'] = company_obj.company_name
            data['company_city_district'] = company_obj.city_district
        
        # 회사 데이터가 있으면 해당 데이터로 설정 (사용자가 입력하지 않았을 때만)
        if company_obj and not data.get('products') and not instance.products:
            data['products'] = company_obj.products
        
        request.data._mutable = True
        request.data.clear()
        request.data.update(data)
        request.data._mutable = False
        
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        # 업데이트 시에도 author, author_name, author_department는 변경하지 않음
        # 회사 정보는 업데이트 가능 (company_obj가 변경되면 company_name, company_city_district도 업데이트)
        company_obj = serializer.validated_data.get('company_obj', serializer.instance.company_obj)
        save_kwargs = {}
        
        if company_obj:
            save_kwargs['company_name'] = company_obj.company_name
            save_kwargs['company_city_district'] = company_obj.city_district
        
        serializer.save(**save_kwargs)

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
    # 회사ID 생성: company_code = 'C'+7자리
    last_code = Company.objects.filter(company_code__startswith='C').aggregate(
        max_code=Max('company_code')
    )['max_code']
    if last_code and last_code[1:].isdigit():
        next_num = int(last_code[1:]) + 1
    else:
        next_num = 1
    new_code = f'C{next_num:07d}'
    company = Company.objects.create(
        company_code=new_code,
        company_name=name,
        customer_classification='신규'
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
                elif best_score >= 0.6:  # 임계값을 0.75에서 0.6으로 낮춤
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
            # 기본 쿼리셋 사용 (select_related는 나중에 최적화)
            queryset = Report.objects.all()
            
            # 검색/필터/정렬
            search = self.request.query_params.get('search', '').strip()
            period = self.request.query_params.get('period', 'all')
            ordering = self.request.query_params.get('ordering', '-visitDate')
            company_id = self.request.query_params.get('companyId', '').strip()

            if company_id:
                # company_code FK는 to_field='company_code'로 설정되어 있으므로 직접 비교 가능
                # company_obj FK도 함께 체크
                # Company 객체를 먼저 찾아서 사용하면 더 정확함
                try:
                    company = Company.objects.get(company_code=company_id)
                    # Company 객체가 있으면 이를 사용하여 필터링
                    # company_obj와 company_code FK 모두 Company 객체로 비교
                    queryset = queryset.filter(
                        Q(company_obj=company) |
                        Q(company_code=company) |
                        Q(company_name=company.company_name)
                    )
                    print(f"[SalesReportListView] companyId 필터링 (Company 객체 사용): {company_id}")
                except Company.DoesNotExist:
                    # Company가 없으면 기존 방식으로 필터링 (문자열 비교)
                    queryset = queryset.filter(
                        Q(company_obj__company_code=company_id) |
                        Q(company_code=company_id) |
                        Q(company_name=company_id)
                    )
                    print(f"[SalesReportListView] companyId 필터링 (문자열 비교): {company_id}")
                except Exception as e:
                    # 기타 예외 발생 시 로깅하고 기존 방식으로 필터링 시도
                    print(f"[SalesReportListView] companyId 필터링 중 예외 발생: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # 안전한 필터링으로 폴백
                    queryset = queryset.filter(
                        Q(company_obj__company_code=company_id) |
                        Q(company_name=company_id)
                    )
            if search:
                queryset = queryset.filter(
                    Q(company_name__icontains=search) |
                    Q(author__username__icontains=search) |
                    Q(author__name__icontains=search) |
                    Q(author_name__icontains=search) |
                    Q(tags__icontains=search)
                )
            if period in ['1m', '3m', '6m']:
                months = int(period[0])
                start_date = timezone.now().date() - timedelta(days=30 * months)
                queryset = queryset.filter(visitDate__gte=start_date)
            queryset = queryset.order_by(ordering)
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
        from django.db import connection
        
        # 회사 코드로 필터링 (company_code 또는 company_code_sap)
        company_code = self.request.query_params.get('company__company_code', None)
        company_code_sap = self.request.query_params.get('company__company_code_sap', None)
        
        # 필터링 조건이 없으면 모든 데이터 반환
        if not company_code and not company_code_sap:
            return models.CompanyFinancialStatus.objects.all()
        
        try:
            # company_code_sap가 주어졌으면 company_code로 변환
            if company_code_sap:
                with connection.cursor() as cursor:
                    try:
                        cx_cursor = cursor.cursor
                        cx_cursor.execute(
                            "SELECT COMPANY_CODE FROM COMPANIES WHERE COMPANY_CODE_SAP = :1",
                            [company_code_sap]
                        )
                        result = cx_cursor.fetchone()
                        if not result:
                            return models.CompanyFinancialStatus.objects.none()
                        company_code = result[0]
                    except Exception:
                        cursor.execute(
                            "SELECT COMPANY_CODE FROM COMPANIES WHERE COMPANY_CODE_SAP = %s",
                            [company_code_sap]
                        )
                        result = cursor.fetchone()
                        if not result:
                            return models.CompanyFinancialStatus.objects.none()
                        company_code = result[0]
            
            # company_code를 사용하여 재무정보 조회
            # company_financial_status.company_id는 COMPANIES.ID (숫자)를 참조하므로
            # JOIN을 사용하여 필터링
            if company_code:
                with connection.cursor() as cursor:
                    try:
                        cx_cursor = cursor.cursor
                        # company_id는 숫자형이고 COMPANIES.ID를 참조
                        cx_cursor.execute("""
                            SELECT CFS.ID 
                            FROM COMPANY_FINANCIAL_STATUS CFS
                            INNER JOIN COMPANIES C ON CFS.COMPANY_ID = C.ID
                            WHERE C.COMPANY_CODE = :1
                        """, [company_code])
                        ids = [row[0] for row in cx_cursor.fetchall()]
                    except Exception:
                        # Django 방식으로 시도
                        cursor.execute("""
                            SELECT CFS.ID 
                            FROM COMPANY_FINANCIAL_STATUS CFS
                            INNER JOIN COMPANIES C ON CFS.COMPANY_ID = C.ID
                            WHERE C.COMPANY_CODE = %s
                        """, [company_code])
                        ids = [row[0] for row in cursor.fetchall()]
                
                if ids:
                    return models.CompanyFinancialStatus.objects.filter(id__in=ids)
                else:
                    return models.CompanyFinancialStatus.objects.none()
            else:
                return models.CompanyFinancialStatus.objects.none()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"CompanyFinancialStatus 필터링 중 오류: {e}", exc_info=True)
            # 오류 발생 시 빈 queryset 반환
            return models.CompanyFinancialStatus.objects.none()
    
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
                Q(company_obj__employee_name__icontains=normalized_name)
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
            'id', 'author_department', 'visitDate', 'company_name', 'company_obj_id', 'type', 
            'products', 'content', 'tags', 'createdAt', 'author_id'
        ).select_related('author').iterator(chunk_size=100)
        
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
                
                # company_obj_id 처리 (Foreign Key이지만 Company의 PK가 company_code(문자열))
                company_code = ''
                try:
                    # 직접 company_obj_id 속성 접근 (문자열 값)
                    if hasattr(report, 'company_obj_id'):
                        company_obj_id_val = report.company_obj_id
                        if company_obj_id_val is not None:
                            company_code = safe_str(company_obj_id_val, '')
                except Exception as e:
                    logging.warning(f'Report ID {report_id}: company_obj_id 접근 오류 - {e}')
                
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
                    'company_obj': company_obj,
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
        if file_extension not in ['csv', 'xlsx']:
            return Response({'error': 'CSV 또는 XLSX 파일만 업로드 가능합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 파일 읽기 (CSV 또는 XLSX)
        if file_extension == 'csv':
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
                # 추가 수치 파싱: 매출이익, 매입금액, 매출단가, 매입단가, 이익율
                def parse_int_safe(val):
                    try:
                        if val is None:
                            return None
                        s = str(val).replace(',', '').replace(' ', '')
                        if s == '':
                            return None
                        return int(float(s))
                    except Exception:
                        return None

                def parse_float_safe(val):
                    try:
                        if val is None:
                            return None
                        s = str(val).replace('%', '').replace(' ', '')
                        if s == '':
                            return None
                        return float(s)
                    except Exception:
                        return None

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
                
                # 회사 연결 시도
                company_obj = None
                거래처명 = row['거래처명'].strip()
                try:
                    # 거래처명으로 회사 찾기
                    company_obj = Company.objects.filter(
                        Q(company_name__icontains=거래처명) |
                        Q(company_code__contains=거래처명)
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
                
                # 각 행을 항상 개별 매출로 저장 (중복 병합 금지)
                SalesData.objects.create(
                    매출일자=매출일자,
                    코드=row.get('코드', '').strip() or None,
                    거래처명=거래처명,
                    매출부서=row.get('매출부서', '').strip() or None,
                    매출담당자=row.get('매출담당자', '').strip() or None,
                    유통형태=row.get('유통형태', '').strip() or None,
                    상품코드=row.get('상품코드', '').strip() or None,
                    상품명=row.get('상품명', '').strip() or None,
                    브랜드=row.get('브랜드', '').strip() or None,
                    축종=row.get('축종', '').strip() or None,
                    부위=row.get('부위', '').strip() or None,
                    원산지=row.get('원산지', '').strip() or None,
                    축종_부위=row.get('축종-부위', '').strip() or None,
                    원산지_축종=row.get('원산지', '').strip() or None,
                    등급=row.get('등급', '').strip() or None,
                    Box=Box,
                    중량_Kg=중량_Kg,
                    매출단가=매출단가_val,
                    매출금액=매출금액,
                    매출이익=매출이익_val,
                    이익율=이익율_val,
                    매입처=row.get('매입 처', '').strip() or None,
                    매입일자=None,   # 필요시 별도 파싱
                    재고보유일=None, # 필요시 별도 파싱
                    수입로컬=row.get('수입/로컬', '').strip() or None,
                    이관재고여부=row.get('이관재고 여부', '').strip() or None,
                    담당자=row.get('담당자', '').strip() or None,
                    매입단가=매입단가_val,
                    매입금액=매입금액_val,
                    지점명=row.get('지점명', '').strip() or None,
                    매출비고=row.get('매출비고', '').strip() or None,
                    매입비고=row.get('매입비고', '').strip() or None,
                    이력번호=row.get('이력번호', '').strip() or None,
                    BL번호=row.get('B/L번호(도체번호)', '').strip() or None,
                    company_obj=company_obj,
                )

                created_count += 1
            
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
    """특정 회사의 최근 6개월 SalesData 조회"""
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
            # 최근 6개월 날짜 범위 계산
            end_date = timezone.now().date()
            current_date = timezone.now()
            all_months = []
            for i in range(6):
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
        
        # 최근 6개월 날짜 범위 계산
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)  # 약 6개월
        
        # 최근 6개월의 모든 달 생성
        all_months = []
        current_date = timezone.now()
        for i in range(6):
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
        
        # 최근 6개월 데이터 정렬
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