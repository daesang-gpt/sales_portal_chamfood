from rest_framework import serializers
from .models import Company, Report, User, CompanyFinancialStatus, SalesData
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CompanySerializer(serializers.ModelSerializer):
    username = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    username_display = serializers.SerializerMethodField()
    class Meta:
        model = Company
        fields = [f.name for f in Company._meta.fields] + ['username_display']

    def get_username_display(self, obj):
        return obj.username.name if obj.username else None

class ReportSerializer(serializers.ModelSerializer):
    company_obj = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        required=False,
        allow_null=True
    )
    author_name = serializers.CharField(source='author.name', read_only=True)
    author_department = serializers.CharField(source='author.department', read_only=True)
    
    # 팀명 매핑을 위한 필드
    team_display = serializers.SerializerMethodField()
    # 회사명 매핑을 위한 필드
    company_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'author', 'author_name', 'author_department', 'team', 'team_display', 'visitDate', 'company', 'company_obj', 'company_display', 'type', 'location', 'products', 'content', 'tags', 'createdAt']
        read_only_fields = ['id', 'createdAt', 'author', 'team']

    def validate(self, data):
        """데이터 검증"""
        print(f"ReportSerializer validate - data: {data}")
        return data

    def get_team_display(self, obj):
        """팀명을 표시용으로 변환"""
        team_mapping = {
            'meat_biz1': '수도권1팀',
            'meat_biz2': '수도권2팀', 
            'meat_biz3': '중부지점'
        }
        return team_mapping.get(obj.team, obj.team)

    def get_company_display(self, obj):
        """회사명을 표시용으로 변환"""
        # 1. company_obj가 있으면 해당 회사의 company_name 사용
        if obj.company_obj:
            return obj.company_obj.company_name
        
        # 2. company_obj가 없으면 company 필드의 값을 Company 모델에서 찾아서 매핑
        try:
            # company 필드가 회사코드인 경우 Company 모델에서 찾기
            company = Company.objects.filter(
                sales_diary_company_code=obj.company
            ).first()
            
            if company:
                return company.company_name
        except:
            pass
        
        # 3. 매핑되지 않으면 원본 company 값 반환
        return obj.company

    def create(self, validated_data):
        # 현재 로그인한 사용자를 author로 설정
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['author'] = request.user
            # 팀명을 사용자의 부서로 자동 설정
            validated_data['team'] = request.user.department
        
        return super().create(validated_data)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'department', 'employee_number', 'role']
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