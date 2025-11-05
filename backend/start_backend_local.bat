@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
set DJANGO_SETTINGS_MODULE=settings.development
echo Starting Django Backend on 0.0.0.0:8000...
echo This will allow connections from all network interfaces
python manage.py runserver 0.0.0.0:8000
