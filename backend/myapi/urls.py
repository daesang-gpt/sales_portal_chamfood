from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ReportViewSet, login_view, register_view, company_stats_view, company_suggest_view, auto_create_company, extract_keywords_view, SalesReportListView, CompanyFinancialStatusViewSet, SalesDataViewSet, download_reports_csv, download_companies_csv, upload_reports_csv, upload_companies_csv, upload_sales_data_csv, dashboard_stats_view, dashboard_charts_data_view
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'company-financial-status', CompanyFinancialStatusViewSet)
router.register(r'sales-data', SalesDataViewSet)

urlpatterns = [
    path('stats/companies/', company_stats_view, name='company-stats'),
    path('stats/dashboard/', dashboard_stats_view, name='dashboard-stats'),
    path('charts/dashboard/', dashboard_charts_data_view, name='dashboard-charts'),
    path('company/suggest/', company_suggest_view, name='company-suggest'),
    path('companies/auto-create/', auto_create_company, name='company-auto-create'),
    path('extract-keywords/', extract_keywords_view, name='extract-keywords'),
    path('sales-reports', SalesReportListView.as_view(), name='sales-report-list'),
    path('export/reports/', download_reports_csv, name='download-reports-csv'),
    path('export/companies/', download_companies_csv, name='download-companies-csv'),
    path('import/reports/', upload_reports_csv, name='upload-reports-csv'),
    path('import/companies/', upload_companies_csv, name='upload-companies-csv'),
    path('import/sales-data/', upload_sales_data_csv, name='upload-sales-data-csv'),
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
] 