# Generated manually for company name search optimization

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0005_remove_company_ceo_remove_company_code_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # MySQL/MariaDB용 인덱스 추가
            "ALTER TABLE companies ADD INDEX idx_company_name (company_name);",
            # 롤백용 SQL
            "ALTER TABLE companies DROP INDEX idx_company_name;"
        ),
    ] 