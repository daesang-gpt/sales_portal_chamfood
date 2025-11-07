"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import os

# dumpdata 실행 시 views import 건너뛰기 (torch DLL 오류 방지)
if os.environ.get('SKIP_VIEWS_IMPORT', 'False').lower() != 'true':
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/', include('myapi.urls')),
    ]
else:
    # dumpdata 실행 시 URL 패턴 비활성화
    urlpatterns = []
