from django.contrib import admin
from .models import Company, Report, User

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'department', 'employee_number', 'role']
    list_filter = ['role', 'department']
    search_fields = ['id', 'name', 'employee_number']
    ordering = ['id']

admin.site.register(Company)
admin.site.register(Report)
