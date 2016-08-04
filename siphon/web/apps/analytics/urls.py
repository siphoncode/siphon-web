
from django.conf.urls import url
from siphon.web.apps.analytics.views import analytics

urlpatterns = [
    url(r'^$', analytics, name='analytics')
]
