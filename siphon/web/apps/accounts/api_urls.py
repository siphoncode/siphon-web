
from django.conf.urls import include, url
from siphon.web.apps.accounts.views import login, info

urlpatterns = [
    url(r'^login/$', login, name='login'),
    url(r'^info/$', info, name='info')
]
