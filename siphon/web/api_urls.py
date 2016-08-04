
from django.conf.urls import include, url

urlpatterns = [
    url(r'^accounts/', include('siphon.web.apps.accounts.api_urls',
        namespace='accounts')),
    url(r'^apps/', include('siphon.web.apps.apps.api_urls',
        namespace='apps')),
    url(r'^bundlers/', include('siphon.web.apps.bundlers.api_urls',
        namespace='bundlers')),
    url(r'^streamers/', include('siphon.web.apps.streamers.api_urls',
        namespace='streamers')),
    url(r'^subscriptions/', include('siphon.web.apps.subscriptions.api_urls',
        namespace='subscriptions')),
    url(r'^submissions/', include('siphon.web.apps.submissions.api_urls',
        namespace='submissions')),
    url(r'^permissions/', include('siphon.web.apps.permissions.api_urls',
        namespace='permissions'))
]
