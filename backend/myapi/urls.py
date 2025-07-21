from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ReportViewSet, login_view, register_view, company_stats_view

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path('stats/companies/', company_stats_view, name='company-stats'),
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
] 