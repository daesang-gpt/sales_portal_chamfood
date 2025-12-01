from django.core.validators import validate_ipv46_address
from rest_framework import serializers
from .models import Company, Report, User, CompanyFinancialStatus, SalesData, AuditLog, ProspectCompany
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import datetime


class OracleDateField(serializers.DateField):
    """Oracle 호환성을 위한 DateField - datetime을 date로 변환"""
    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.date().isoformat()
        elif isinstance(value, datetime.date):
            return value.isoformat()
        return super().to_representation(value)

class CompanySerializer(serializers.ModelSerializer):
    # Oracle 호환성을 위해 DateField를 커스텀 필드로 교체
    established_date = OracleDateField(required=False, allow_null=True)
    code_create_date = OracleDateField(required=False, allow_null=True)
    transaction_start_date = OracleDateField(required=False, allow_null=True)
    
    class Meta:
        model = Company
        fields = [
            'company_code', 'company_name', 'customer_classification', 'company_type',
            'tax_id', 'established_date', 'ceo_name', 'head_address', 'city_district',
            'processing_address', 'main_phone', 'industry_name', 'products', 'website',
            'remarks', 'sap_code_type', 'company_code_sap', 'biz_code', 'biz_name',
            'department_code', 'department', 'employee_number', 'employee_name',
            'distribution_type_sap_code', 'distribution_type_sap', 'contact_person',
            'contact_phone', 'code_create_date', 'transaction_start_date', 'payment_terms'
        ]

class ReportSerializer(serializers.ModelSerializer):
    # company_obj는 제거되었고, company_code FK만 사용
    # 프론트엔드 호환성을 위해 company_obj 필드는 유지하되, 내부적으로는 company_code로 매핑
    # 쓰기 가능한 필드로 추가 (업데이트 시 사용)
    company_obj = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        write_only=True  # 쓰기 전용으로 변경
    )
    
    # 실제 company_code FK 필드 (쓰기 가능)
    company_code_fk = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
        source='company_code'  # Report 모델의 company_code FK 필드와 매핑
    )
    
    # 작성자 정보 (저장된 필드와 관련 User 모델 정보 둘 다 제공)
    author_username = serializers.SerializerMethodField()
    author_name_from_user = serializers.SerializerMethodField()
    author_department_from_user = serializers.SerializerMethodField()
    
    # 회사 정보 (저장된 필드와 관련 Company 모델 정보 둘 다 제공)
    # 회사코드는 문자열 코드로 반환 (FK id가 아닌 실제 company_code)
    company_code = serializers.SerializerMethodField()
    company_code_resolved = serializers.SerializerMethodField()
    company_name_from_obj = serializers.SerializerMethodField()
    company_city_district_from_obj = serializers.SerializerMethodField()
    
    # Oracle 호환성을 위해 DateField를 커스텀 필드로 교체
    visitDate = OracleDateField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'author', 'author_username', 'author_name', 'author_name_from_user',
            'author_department', 'author_department_from_user', 'visitDate',
            'company_obj', 'company_code_fk', 'company_code', 'company_code_resolved', 'company_name', 'company_name_from_obj',
            'company_city_district', 'company_city_district_from_obj',
            'sales_stage', 'type', 'products', 'content', 'tags', 'createdAt'
        ]
        read_only_fields = ['id', 'createdAt', 'author', 'author_name', 'author_department']
    
    def to_representation(self, instance):
        """출력 시 company_obj 필드에 값을 설정"""
        representation = super().to_representation(instance)
        # company_obj를 읽기 전용으로 출력 (company_code 값 사용)
        representation['company_obj'] = representation.get('company_code')
        return representation

    def validate(self, data):
        """데이터 검증"""
        return data

    def create(self, validated_data):
        # company_obj는 프론트엔드 호환성을 위한 필드이므로 제거
        if 'company_obj' in validated_data:
            validated_data.pop('company_obj')
        
        # author 필드가 있으면 제거 (perform_create에서 author_id로 처리됨)
        if 'author' in validated_data:
            validated_data.pop('author')
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # 업데이트 시에도 회사 표시/코드 동기화
        # company_obj는 문자열 company_code로 받아서 처리
        print(f"[ReportSerializer.update] ========== ReportSerializer update 시작 ==========")
        print(f"[ReportSerializer.update] 기존 instance.company_code: {instance.company_code}")
        print(f"[ReportSerializer.update] 기존 instance.company_name: {instance.company_name}")
        print(f"[ReportSerializer.update] validated_data: {validated_data}")
        
        if 'company_obj' in validated_data:
            company_code_value = validated_data.pop('company_obj')
            print(f"[ReportSerializer.update] company_obj 값: {company_code_value} (타입: {type(company_code_value)})")
            if isinstance(company_code_value, Company):
                # Company 객체인 경우
                instance.company_code = company_code_value
                validated_data['company_name'] = company_code_value.company_name
                validated_data['company_city_district'] = company_code_value.city_district
            elif company_code_value:
                # 문자열 company_code를 Company 객체로 변환
                if isinstance(company_code_value, str) and company_code_value.strip():
                    try:
                        company = Company.objects.get(company_code=company_code_value)
                        # ForeignKey 필드에 Company 객체 설정 - 직접 할당하지 말고 validated_data에 추가
                        validated_data['company_code'] = company  # Company 객체를 validated_data에 설정
                        validated_data['company_name'] = company.company_name
                        validated_data['company_city_district'] = company.city_district
                        print(f"[ReportSerializer.update] Company 객체로 업데이트: {company.company_code} - {company.company_name}")
                        print(f"[ReportSerializer.update] validated_data에 company_code 설정: {company}")
                    except Company.DoesNotExist:
                        # 존재하지 않는 회사 코드인 경우 ValidationError 발생
                        raise serializers.ValidationError({
                            'company_obj': f'회사코드 "{company_code_value}"가 존재하지 않습니다.'
                        })
                else:
                    # 빈 문자열이거나 None인 경우
                    instance.company_code = None
                    # company_name과 company_city_district도 제거
                    validated_data.pop('company_name', None)
                    validated_data.pop('company_city_district', None)
        
        # company_code가 validated_data에 직접 포함된 경우 (views.py에서 설정한 경우)
        if 'company_code' in validated_data:
            company_code_value = validated_data.pop('company_code')
            if isinstance(company_code_value, Company):
                # Company 객체인 경우
                instance.company_code = company_code_value
                if 'company_name' not in validated_data:
                    validated_data['company_name'] = company_code_value.company_name
                if 'company_city_district' not in validated_data:
                    validated_data['company_city_district'] = company_code_value.city_district
            elif isinstance(company_code_value, str) and company_code_value.strip():
                try:
                    company = Company.objects.get(company_code=company_code_value)
                    instance.company_code = company
                    if 'company_name' not in validated_data:
                        validated_data['company_name'] = company.company_name
                    if 'company_city_district' not in validated_data:
                        validated_data['company_city_district'] = company.city_district
                except Company.DoesNotExist:
                    raise serializers.ValidationError({
                        'company_code': f'회사코드 "{company_code_value}"가 존재하지 않습니다.'
                    })
            elif not company_code_value:
                instance.company_code = None
                # company_name과 company_city_district도 제거
                validated_data.pop('company_name', None)
                validated_data.pop('company_city_district', None)
        
        # 업데이트 완료 후 로그
        print(f"[ReportSerializer.update] super().update() 호출 전")
        print(f"[ReportSerializer.update] 최종 validated_data: {validated_data}")
        try:
            updated_instance = super().update(instance, validated_data)
            print(f"[ReportSerializer.update] super().update() 호출 후")
            print(f"[ReportSerializer.update] 최종 업데이트 완료")
            print(f"[ReportSerializer.update] updated_instance.company_code: {updated_instance.company_code}")
            print(f"[ReportSerializer.update] updated_instance.company_name: {updated_instance.company_name}")
            print(f"[ReportSerializer.update] ========== ReportSerializer update 끝 ==========")
            return updated_instance
        except Exception as e:
            # 디버깅을 위한 로그 출력
            import traceback
            print(f"[ReportSerializer.update] 오류 발생: {e}")
            print(f"[ReportSerializer.update] instance.company_code: {instance.company_code}")
            print(f"[ReportSerializer.update] validated_data: {validated_data}")
            print(traceback.format_exc())
            raise

    def get_company_code_resolved(self, obj):
        try:
            # company_code FK를 먼저 확인
            if obj.company_code:
                # Company 객체인 경우
                if hasattr(obj.company_code, 'company_code'):
                    return obj.company_code.company_code
                # 문자열인 경우
                if isinstance(obj.company_code, str):
                    return obj.company_code
                # 기타 경우 문자열로 변환
                return str(obj.company_code)
            
            # Fallback: resolve by company_name and city
            name = (obj.company_name or '').strip()
            city = (obj.company_city_district or '').strip()
            if not name:
                return None
            
            from .models import Company
            # 먼저 company_name + city_district로 찾기
            if city:
                comp = Company.objects.filter(company_name=name, city_district=city).first()
                if comp:
                    return comp.company_code
            
            # company_name만으로 찾기
            comp = Company.objects.filter(company_name=name).first()
            if comp:
                return comp.company_code
            
            return None
        except Exception as e:
            # 디버깅을 위한 로그 출력
            import traceback
            print(f"[get_company_code_resolved] 오류 발생: {e}")
            print(f"[get_company_code_resolved] obj.company_code: {getattr(obj, 'company_code', None)}")
            print(f"[get_company_code_resolved] obj.company_name: {getattr(obj, 'company_name', None)}")
            print(traceback.format_exc())
            return None

    def get_author_username(self, obj):
        try:
            return obj.author.username if obj.author else None
        except Exception:
            return None
    
    def get_author_name_from_user(self, obj):
        try:
            return obj.author.name if obj.author else None
        except Exception:
            return None
    
    def get_author_department_from_user(self, obj):
        try:
            return obj.author.department if obj.author else None
        except Exception:
            return None
    
    def get_company_name_from_obj(self, obj):
        try:
            # company_code FK를 통해 Company 객체 가져오기
            if obj.company_code:
                return obj.company_code.company_name if hasattr(obj.company_code, 'company_name') else None
            return None
        except Exception:
            return None
    
    def get_company_city_district_from_obj(self, obj):
        try:
            # company_code FK를 통해 Company 객체 가져오기
            if obj.company_code:
                return obj.company_code.city_district if hasattr(obj.company_code, 'city_district') else None
            return None
        except Exception:
            return None

    def get_company_code(self, obj):
        try:
            # company_code FK를 통해 실제 문자열 코드 반환
            # 먼저 company_code FK 확인
            company_code_fk = getattr(obj, 'company_code', None)
            
            if company_code_fk:
                # Company 인스턴스인 경우
                if hasattr(company_code_fk, 'company_code'):
                    return company_code_fk.company_code
                # pk 속성이 있는 경우
                if hasattr(company_code_fk, 'pk'):
                    pk_value = company_code_fk.pk
                    if pk_value:
                        return str(pk_value)
                # 문자열인 경우
                if isinstance(company_code_fk, str):
                    return company_code_fk
                # 기타 경우 문자열로 변환
                return str(company_code_fk)
            
            # company_code FK가 없으면 company_name과 company_city_district로 찾기
            resolved_code = self.get_company_code_resolved(obj)
            if resolved_code:
                return resolved_code
            
            # 모든 방법이 실패하면 None 반환
            return None
        except Exception as e:
            # 디버깅을 위한 로그 출력
            import traceback
            print(f"[get_company_code] 오류 발생: {e}")
            print(f"[get_company_code] obj.company_code: {getattr(obj, 'company_code', None)}")
            print(f"[get_company_code] obj.company_name: {getattr(obj, 'company_name', None)}")
            print(f"[get_company_code] obj.company_city_district: {getattr(obj, 'company_city_district', None)}")
            print(traceback.format_exc())
            # fallback 해석
            try:
                return self.get_company_code_resolved(obj)
            except:
                return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'department', 'employee_number', 'role', 'email']
        read_only_fields = ['id', 'role']

class LoginSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)

class ForgotPasswordSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)
    confirm_password = serializers.CharField(max_length=128, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '새 비밀번호가 일치하지 않습니다.'})
        
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({'new_password': '비밀번호는 최소 8자 이상이어야 합니다.'})
        
        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'password', 'name', 'department', 'employee_number', 'role', 'email']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            name=validated_data['name'],
            department=validated_data['department'],
            employee_number=validated_data['employee_number'],
            role=validated_data.get('role', 'user'),
            email=validated_data.get('email', '')
        )
        return user 

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token 

class CompanyFinancialStatusSerializer(serializers.ModelSerializer):
    company_code = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_code_sap = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    
    # Oracle 호환성을 위해 DateField를 커스텀 필드로 교체
    fiscal_year = OracleDateField()
    
    class Meta:
        model = CompanyFinancialStatus
        fields = [
            'id', 'company', 'company_code', 'company_name', 'company_code_sap',
            'fiscal_year', 'total_assets', 'capital', 'total_equity',
            'revenue', 'operating_income', 'net_income'
        ]
        read_only_fields = ['id', 'company', 'company_code', 'company_name', 'company_code_sap']
    
    def get_company(self, obj):
        """company 필드를 안전하게 처리 - company_code 반환"""
        try:
            if hasattr(obj, 'company') and obj.company:
                return obj.company.company_code
            return None
        except Exception:
            try:
                # company 접근 실패 시 company_id가 있으면 그대로 반환 (필요시 나중에 조회)
                if hasattr(obj, 'company_id') and obj.company_id:
                    return obj.company_id
                return None
            except Exception:
                return None
    
    def get_company_code(self, obj):
        try:
            if hasattr(obj, 'company') and obj.company:
                return obj.company.company_code
            return None
        except Exception:
            return None
    
    def get_company_name(self, obj):
        try:
            if hasattr(obj, 'company') and obj.company:
                return obj.company.company_name
            return None
        except Exception:
            return None
    
    def get_company_code_sap(self, obj):
        try:
            if hasattr(obj, 'company') and obj.company:
                return obj.company.company_code_sap
            return None
        except Exception:
            return None

class SalesDataSerializer(serializers.ModelSerializer):
    # Oracle 호환성을 위해 DateField를 커스텀 필드로 교체
    매출일자 = OracleDateField()
    매입일자 = OracleDateField(required=False, allow_null=True)
    
    class Meta:
        model = SalesData
        fields = [
            'id', '매출일자', '코드', '거래처명', '매출부서', '매출담당자', '유통형태', 
            '상품코드', '상품명', '브랜드', '축종', '부위', '원산지', '축종_부위', 
            '원산지_축종', '등급', 'Box', '중량_Kg', '매출단가', '매출금액', 
            '매출이익', '이익율', '매입처', '매입일자', '재고보유일', '수입로컬', 
            '이관재고여부', '담당자', '매입단가', '매입금액', '지점명', '매출비고', 
            '매입비고', '이력번호', 'BL번호', 'created_at'
        ] 
        read_only_fields = ['id', 'created_at']

class SafeIPAddressField(serializers.CharField):
    """Django 3.2 + DRF 조합에서 IP 필드 직렬화/역직렬화 시 발생하는 호환성 문제를 해결한다."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('allow_null', True)
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return value or None

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if not value:
            return value
        try:
            validate_ipv46_address(value)
        except Exception:
            raise serializers.ValidationError('유효한 IP 주소를 입력하세요.')
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    target_username = serializers.CharField(source='target_user.username', read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    # Django 3.2 + DRF 조합에서 GenericIPAddressField 사용 시 unpack 오류가 발생하므로
    # 직접 정의한 SafeIPAddressField로 대체해 검증과 직렬화를 모두 안전하게 처리한다.
    ip_address = SafeIPAddressField(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'action_type', 'action_type_display', 'description',
            'ip_address', 'user_agent', 'target_user', 'target_username',
            'old_value', 'new_value', 'resource_type', 'resource_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ProspectCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProspectCompany
        fields = [
            'id', 'license_number', 'company_name', 'industry', 'ceo_name',
            'location', 'main_products', 'phone', 'priority', 'has_transaction',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at'] 