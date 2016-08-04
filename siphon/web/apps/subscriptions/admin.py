
from django.contrib import admin
from siphon.web.apps.subscriptions.models import Plan, Subscription, \
    ChargebeeEvent

admin.site.register(Plan)
admin.site.register(Subscription)
admin.site.register(ChargebeeEvent)
