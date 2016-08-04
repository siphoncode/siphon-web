
from django.conf.urls import url
from siphon.web.apps.permissions.views import InvitationView

urlpatterns = [
    url(r'^accept-invite/(?P<invite_code>[\w\-_]+)+$',
        InvitationView.as_view(), name='accept-invite')
]
