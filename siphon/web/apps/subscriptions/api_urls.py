

from django.conf.urls import url
from siphon.web.apps.subscriptions.views import chargebee_webhook

urlpatterns = [
    url(r'^chargebee_webhook/$', chargebee_webhook, name='chargebee_webhook')
]
