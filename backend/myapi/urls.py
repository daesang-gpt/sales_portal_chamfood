from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ReportViewSet, login_view, register_view, company_stats_view, company_suggest_view, auto_create_company, extract_keywords_view, SalesReportListView, CompanyFinancialStatusViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'company-financial-status', CompanyFinancialStatusViewSet)

urlpatterns = [
    path('stats/companies/', company_stats_view, name='company-stats'),
    path('company/suggest/', company_suggest_view, name='company-suggest'),
    path('companies/auto-create/', auto_create_company, name='company-auto-create'),
    path('extract-keywords/', extract_keywords_view, name='extract-keywords'),
    path('sales-reports', SalesReportListView.as_view(), name='sales-report-list'),
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
] 