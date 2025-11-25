from django.apps import AppConfig


class MyapiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapi'
    
    def ready(self):
        import myapi.signals  # 시그널 등록