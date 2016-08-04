
from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView

from siphon.web.apps.docs.views import BaseVersionView

# Note: the index route redirects for quickstart for now, but later
# we'll have a real page index here when more content exists.
urlpatterns = [
    url(r'^$',
        RedirectView.as_view(pattern_name='docs:quickstart', permanent=False),
        name='index'),
    url(r'^quickstart/$',
        TemplateView.as_view(template_name='docs/quickstart.html'),
        name='quickstart'),
    url(r'^build-a-chat-app/$',
        TemplateView.as_view(template_name='docs/chat-app.html'),
        name='chat-app'),
    url(r'^build-a-youtube-browser/$',
        TemplateView.as_view(template_name='docs/youtube-browser.html'),
        name='youtube-browser'),
    url(r'^run-react-native-on-device/$',
        TemplateView.as_view(template_name='docs/run-on-device.html'),
        name='run-on-device'),
    url(r'^faq/$',
        TemplateView.as_view(template_name='docs/faq.html'),
        name='faq'),
    url(r'^facebook-sdk/$',
        TemplateView.as_view(template_name='docs/facebook-sdk.html'),
        name='facebook-sdk'),
    url(r'^team-sharing/$',
        TemplateView.as_view(template_name='docs/team-sharing.html'),
        name='team-sharing'),
    url(r'^beta-testing/$',
        TemplateView.as_view(template_name='docs/beta-testing.html'),
        name='beta-testing'),
    url(r'^existing-react-native-app/$',
        TemplateView.as_view(
            template_name='docs/existing-react-native-app.html'),
        name='existing-react-native-app'),
    url(r'^base-version/$', BaseVersionView.as_view(), name='base-version')
]
