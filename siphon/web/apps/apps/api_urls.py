
from django.conf.urls import include, url
from siphon.web.apps.apps.views import AppList

urlpatterns = [
    url(r'^(?P<app_id>[\w\-_]+)?$', AppList.as_view(), name='apps'),
]
