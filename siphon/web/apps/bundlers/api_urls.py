
from django.conf.urls import include, url
from siphon.web.apps.bundlers.views import bundlers

urlpatterns = [
    url(r'^$', bundlers, name='bundlers')
]