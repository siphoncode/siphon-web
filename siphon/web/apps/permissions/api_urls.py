
from django.conf.urls import url
from siphon.web.apps.permissions.views import PermissionView

urlpatterns = [
    url(r'^$', PermissionView.as_view(), name='permissions'),
]
