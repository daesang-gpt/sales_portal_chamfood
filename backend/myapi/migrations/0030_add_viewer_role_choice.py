from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0029_update_customer_classification_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('admin', '관리자'), ('user', '사용자'), ('viewer', '뷰어')],
                default='user',
                max_length=10,
            ),
        ),
    ]

