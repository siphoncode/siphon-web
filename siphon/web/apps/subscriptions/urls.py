

from django.conf.urls import url
from siphon.web.apps.subscriptions.views import checkout_redirect

urlpatterns = [
    url(r'^checkout/(?P<plan_id>[\w\-_]+)+$', checkout_redirect, name='plan_redirect')
]
