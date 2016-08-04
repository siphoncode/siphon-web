
from django.conf.urls import include, url
from siphon.web.apps.streamers.views import streamers

urlpatterns = [
    url(r'^$', streamers, name='streamers')
]
