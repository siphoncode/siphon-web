
from django.conf.urls import url
from siphon.web.apps.submissions.views import SubmissionView, \
    CheckSubmissionView, ValidateAppView

urlpatterns = [
    url(r'^$', SubmissionView.as_view(), name='submissions'),
    url(r'^check/$', CheckSubmissionView.as_view(), name='check'),
    url(r'^validate/$', ValidateAppView.as_view(), name='validate')
]
