from rest_framework import serializers
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CompanySerializer(serializers.ModelSerializer):
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
    company_obj = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False,
        allow_null=True
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
    
    class Meta:
        model = Report
        fields = [
            'id', 'author', 'author_username', 'author_name', 'author_name_from_user',
            'author_department', 'author_department_from_user', 'visitDate',
            'company_obj', 'company_code', 'company_code_resolved', 'company_name', 'company_name_from_obj',
            'company_city_district', 'company_city_district_from_obj',
            'sales_stage', 'type', 'products', 'content', 'tags', 'createdAt'
        ]
        read_only_fields = ['id', 'createdAt', 'author', 'author_name', 'author_department']

    def validate(self, data):
        """데이터 검증"""
        print("\n" + "=" * 80)
        print("[ReportSerializer.validate] 시작")
        print("=" * 80)
        print(f"[ReportSerializer.validate] data keys: {list(data.keys())}")
        print("\n[ReportSerializer.validate] data 상세:")
        for key, value in data.items():
            value_type = type(value)
            if isinstance(value, str) and len(value) > 100:
                value_repr = value[:100] + "..."
            else:
                value_repr = repr(value)
            print(f"  {key}: {value_repr} (type: {value_type})")
        print("=" * 80 + "\n")
        return data

    def create(self, validated_data):
        print("\n" + "=" * 80)
        print("[ReportSerializer.create] 시작")
        print("=" * 80)
        
        # perform_create에서 이미 모든 필드를 설정하므로 여기서는 추가 설정만 수행
        # author는 perform_create에서 author_id로 설정되므로 여기서는 건드리지 않음
        
        print(f"[ReportSerializer.create] validated_data keys (처음): {list(validated_data.keys())}")
        print("\n[ReportSerializer.create] validated_data 상세 (처음):")
        for key, value in validated_data.items():
            value_type = type(value)
            if isinstance(value, str) and len(value) > 100:
                value_repr = value[:100] + "..."
            else:
                value_repr = repr(value)
            print(f"  {key}: {value_repr} (type: {value_type})")
            if hasattr(value, 'pk'):
                print(f"    -> pk: {value.pk} (type: {type(value.pk)})")
            if hasattr(value, 'id'):
                print(f"    -> id: {value.id} (type: {type(value.id)})")
        
        # 회사 정보 처리
        # perform_create에서 save_kwargs로 company_code를 문자열로 전달하므로
        # 여기서는 Company 객체를 문자열로 변환만 수행
        company_obj = validated_data.get('company_obj')
        
        # company_code 처리: Company 객체면 무조건 문자열로 변환
        if 'company_code' in validated_data:
            company_code_value = validated_data['company_code']
            if isinstance(company_code_value, Company):
                # Company 객체면 문자열로 변환
                validated_data['company_code'] = company_code_value.company_code
                print(f"[ReportSerializer.create] company_code를 Company 객체에서 문자열로 변환: {company_code_value.company_code}")
            elif isinstance(company_code_value, str):
                print(f"[ReportSerializer.create] company_code는 이미 문자열: {company_code_value}")
            else:
                print(f"[ReportSerializer.create] company_code 타입 확인: {type(company_code_value)}")
        
        # company_obj도 제거 (company_obj_id로 대체됨)
        if 'company_obj' in validated_data:
            old_company_obj = validated_data.pop('company_obj')
            print(f"[ReportSerializer.create] company_obj 제거됨 (company_obj_id로 대체)")
        
        # author 필드가 있으면 제거 (perform_create에서 author_id로 처리됨)
        if 'author' in validated_data:
            removed_author = validated_data.pop('author')
            print(f"[ReportSerializer.create] author 필드 제거됨: {removed_author}")
        
        print(f"\n[ReportSerializer.create] validated_data keys (최종): {list(validated_data.keys())}")
        print("\n[ReportSerializer.create] validated_data 상세 (최종):")
        for key, value in validated_data.items():
            value_type = type(value)
            if isinstance(value, str) and len(value) > 100:
                value_repr = value[:100] + "..."
            else:
                value_repr = repr(value)
            print(f"  {key}: {value_repr} (type: {value_type})")
            if hasattr(value, 'pk'):
                print(f"    -> pk: {value.pk} (type: {type(value.pk)})")
            if hasattr(value, 'id'):
                print(f"    -> id: {value.id} (type: {type(value.id)})")
        
        print("\n[ReportSerializer.create] super().create() 호출 시작...")
        try:
            result = super().create(validated_data)
            print(f"[ReportSerializer.create] super().create() 성공! result: {result}")
            print(f"[ReportSerializer.create] result.id: {getattr(result, 'id', 'N/A')}")
            print("=" * 80 + "\n")
            return result
        except Exception as e:
            print("\n" + "=" * 80)
            print("[ReportSerializer.create] super().create() 중 오류 발생!")
            print(f"오류 타입: {type(e).__name__}")
            print(f"오류 메시지: {str(e)}")
            print("\n상세 스택 트레이스:")
            import traceback
            traceback.print_exc()
            print("=" * 80 + "\n")
            raise
    
    def update(self, instance, validated_data):
        # 업데이트 시에도 회사 표시/코드 동기화
        company_obj = validated_data.get('company_obj', instance.company_obj)
        if company_obj:
            validated_data['company_name'] = company_obj.company_name
            validated_data['company_city_district'] = company_obj.city_district
            validated_data['company_code'] = company_obj
        
        return super().update(instance, validated_data)

    def get_company_code_resolved(self, obj):
        try:
            if obj.company_obj:
                return obj.company_obj.company_code
            # Fallback: resolve by company_name and city
            name = (obj.company_name or '').strip()
            city = (obj.company_city_district or '').strip()
            if not name:
                return None
            from .models import Company
            if city:
                comp = Company.objects.filter(company_name=name, city_district=city).first()
                if comp:
                    return comp.company_code
            comp = Company.objects.filter(company_name=name).first()
            return comp.company_code if comp else None
        except Exception:
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
            return obj.company_obj.company_name if obj.company_obj else None
        except Exception:
            return None
    
    def get_company_city_district_from_obj(self, obj):
        try:
            return obj.company_obj.city_district if obj.company_obj else None
        except Exception:
            return None

    def get_company_code(self, obj):
        try:
            # 1) 새 FK 관계를 통해 실제 문자열 코드 반환
            if hasattr(obj, 'company_code') and obj.company_code:
                # obj.company_code는 Company 인스턴스
                return getattr(obj.company_code, 'company_code', None)
            # 2) company_obj가 있으면 그 코드
            if obj.company_obj:
                return obj.company_obj.company_code
            # 3) fallback 해석
            return self.get_company_code_resolved(obj)
        except Exception:
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
    company_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesData
        fields = [
            'id', '매출일자', '코드', '거래처명', '매출부서', '매출담당자', '유통형태', 
            '상품코드', '상품명', '브랜드', '축종', '부위', '원산지', '축종_부위', 
            '원산지_축종', '등급', 'Box', '중량_Kg', '매출단가', '매출금액', 
            '매출이익', '이익율', '매입처', '매입일자', '재고보유일', '수입로컬', 
            '이관재고여부', '담당자', '매입단가', '매입금액', '지점명', '매출비고', 
            '매입비고', '이력번호', 'BL번호', 'company_obj', 'created_at', 'company_name'
        ] 
        read_only_fields = ['id', 'created_at', 'company_name']

    def get_company_name(self, obj):
        return obj.company_obj.company_name if obj.company_obj else obj.거래처명 