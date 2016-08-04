
from django.contrib.auth.views import logout
from django.conf.urls import include, url

from siphon.web.apps.accounts.views import LoginView, RegisterView

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^logout/$', logout, {'next_page': '/'}, name='logout')
]
