from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Подключаем сигнал, который выполнится после миграций
        from .auto_permissions import auto_sync_permissions
        post_migrate.connect(auto_sync_permissions, sender=self)
