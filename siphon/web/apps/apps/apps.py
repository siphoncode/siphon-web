
from django.apps import AppConfig

class AppsConfig(AppConfig):
    name = 'siphon.web.apps.apps'
    verbose_name = 'Apps'

    def ready(self):
        from siphon.web.apps.apps.signals.handlers import send_app_notification
