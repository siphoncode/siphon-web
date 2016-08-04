from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.decorators import login_required


def static_url(regex, name, authenticated=False):
    view = TemplateView.as_view(template_name='%s.html' % name)
    if authenticated:
        view = login_required(view)
    return url(regex, view, name=name)

static_urls = [
    static_url(r'^$', 'landing'),
    static_url(r'^dashboard/$', 'dashboard', authenticated=True),
    static_url(r'^contact-us/$', 'contact'),
    static_url(r'^pricing/$', 'pricing'),
    static_url(r'^terms-of-use/$', 'terms-of-use'),
    static_url(r'^privacy-policy/$', 'privacy-policy'),
    static_url(r'^android-launch/$', 'android-launch')
]

urlpatterns = [
    url('', include(static_urls, namespace='static')),
    url(r'^docs/', include('siphon.web.apps.docs.urls',
        namespace='docs')),
    url(r'^accounts/', include('siphon.web.apps.accounts.urls',
        namespace='accounts')),
    url(r'^subscriptions/', include('siphon.web.apps.subscriptions.urls',
        namespace='subscriptions')),
    url(r'^analytics/', include('siphon.web.apps.analytics.urls',
        namespace='analytics')),
    url(r'^permissions/', include('siphon.web.apps.permissions.urls',
        namespace='permissions')),

    # API
    url(r'^api/v1/', include('siphon.web.api_urls', namespace='api')),

    # App Store shortcut alias
    url(r'^i/?$', RedirectView.as_view(
        url='https://itunes.apple.com/us/app/siphon-sandbox/id1059664078',
        permanent=False
    )),

    # Play Store shortcut alias
    url(r'^a/?$', RedirectView.as_view(
        url='https://play.google.com/store/apps/details?id=com.getsiphon.siphonbase',
        permanent=False
    )),

    # Third-party
    url(r'^drip/', include('drip.urls', namespace='drip')),

    # Here be dragons
    url(r'^bananas/', include(admin.site.urls))
]
