import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from myapi.models import User

admin = User.objects.filter(username='admin').first()
if admin:
    admin.set_password('admin1234')
    admin.save()
    print('Admin password reset to: admin1234')
    from django.contrib.auth import authenticate
    if authenticate(username='admin', password='admin1234'):
        print('Login test: SUCCESS')
    else:
        print('Login test: FAILED')
else:
    print('Admin user not found')

