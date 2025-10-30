from rest_framework import serializers
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    company_obj = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False,
        allow_null=True
    )
    
    # 작성자 정보 (저장된 필드와 관련 User 모델 정보 둘 다 제공)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_name_from_user = serializers.CharField(source='author.name', read_only=True)
    author_department_from_user = serializers.CharField(source='author.department', read_only=True)
    
    # 회사 정보 (저장된 필드와 관련 Company 모델 정보 둘 다 제공)
    # 회사코드는 문자열 코드로 반환 (FK id가 아닌 실제 company_code)
    company_code = serializers.SerializerMethodField()
    company_code_resolved = serializers.SerializerMethodField()
    company_name_from_obj = serializers.CharField(source='company_obj.company_name', read_only=True, allow_null=True)
    company_city_district_from_obj = serializers.CharField(source='company_obj.city_district', read_only=True, allow_null=True)
    
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
        print(f"ReportSerializer validate - data: {data}")
        return data

    def create(self, validated_data):
        # 현재 로그인한 사용자를 author로 설정하고 작성자명, 팀명 저장
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            validated_data['author'] = user
            validated_data['author_name'] = user.name
            validated_data['author_department'] = user.department
            
            # 회사 정보 저장
            company_obj = validated_data.get('company_obj')
            if company_obj:
                validated_data['company_name'] = company_obj.company_name
                validated_data['company_city_district'] = company_obj.city_district
                # 새 FK도 함께 설정 (문자열 PK)
                validated_data['company_code'] = company_obj
        
        return super().create(validated_data)
    
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
        fields = ['id', 'username', 'name', 'department', 'employee_number', 'role']
        read_only_fields = ['id', 'role']

class LoginSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'password', 'name', 'department', 'employee_number', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            name=validated_data['name'],
            department=validated_data['department'],
            employee_number=validated_data['employee_number'],
            role=validated_data.get('role', 'user')
        )
        return user 

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        return token 

class CompanyFinancialStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyFinancialStatus
        fields = '__all__'

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