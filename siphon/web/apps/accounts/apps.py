
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'siphon.web.apps.accounts'
    verbose_name = 'Accounts'

    def ready(self):
        from siphon.web.apps.accounts.signals.handlers import create_user_token