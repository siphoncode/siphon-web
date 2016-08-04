
import json
import requests
import traceback
import logging
logger = logging.getLogger('django')

from django.contrib.auth.models import User
from django.views.generic import View
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseNotFound, HttpResponseBadRequest

from siphon.web.apps.subscriptions.models import Plan, Subscription, ChargebeeEvent

HANDLED_EVENTS = (
    'subscription_created', 'subscription_started', 'subscription_activated',
    'subscription_changed', 'subscription_cancelled',
    'subscription_reactivated', 'subscription_renewed',
    'subscription_scheduled_cancellation_removed'
)

class ChargebeeError(Exception):
    pass


def get_chargebee_event(event_id):
    url = '%s/api/v1/events/%s' % (
        settings.CHARGEBEE_SITE, event_id)
    resp = requests.get(url, auth=(settings.CHARGEBEE_API_KEY, ''))
    return resp.json()['event']

@login_required
@require_http_methods(['GET'])
def checkout_redirect(request, plan_id):
    try:
        Plan.objects.get(plan_id=plan_id)
    except Plan.DoesNotExist:
        return HttpResponseNotFound('Unknown plan: %s' % plan_id)
    user = request.user
    url = '%s/hosted_pages/plans/%s?customer[id]=%s&customer[email]=%s' % (
        settings.CHARGEBEE_SITE, plan_id, user.username, user.email)
    return HttpResponseRedirect(url)

@csrf_exempt
@require_http_methods(['POST'])
def chargebee_webhook(request):
    logger.info('[webhook] %s' % str(request.body))
    obj = json.loads(request.body.decode('utf-8'))
    content = obj['content']

    # Don't trust the caller, verify the event data by fetching it
    # from the Chargebee API directly. Then store it raw in the database
    # for future reference.
    try:
        event_id = obj['id']
        obj = get_chargebee_event(event_id)
        event_type = obj['event_type']
    except KeyError as e:
        logger.info('[webhook] error: %s\n\n%s' % (
            str(e), traceback.format_exc()))
        return HttpResponseBadRequest()
    ChargebeeEvent(name=event_type, raw_content=json.dumps(obj)).save()

    if event_type not in HANDLED_EVENTS:
        logger.info('[webhook] ignoring: %s' % event_type)
        return HttpResponse() # Chargebee wants a 200 OK back

    # Check that the user and plan associated with this event exist.
    customer_id = content['customer']['id']
    plan_id = content['subscription']['plan_id']
    try:
        user = User.objects.get(username=customer_id)
        plan = Plan.objects.get(plan_id=plan_id)
    except User.DoesNotExist:
        logger.error('[webhook] unknown username: %s' % customer_id)
        raise
    except Plan.DoesNotExist:
        logger.error('[webhook] unknown plan: %s' % plan_id)
        raise

    # Try to get a subscription object for this user, otherwise create one.
    subscription_id = content['subscription']['id']
    try:
        subscription = Subscription.objects.get(user=user)
        # If we already have a subscription, do a sanity check.
        if subscription.plan.plan_id != plan_id:
            raise ChargebeeError('Plan mismatch: %s != %s' % (
                subscription.plan.plan_id, plan_id))
        if subscription.chargebee_id != subscription_id:
            raise ChargebeeError('Subscription mismatch: %s != %s' % (
                subscription.chargebee_id, subscription_id))
    except Subscription.DoesNotExist:
        # This is a new subscription
        subscription = Subscription(
            user=user,
            plan=plan,
            chargebee_id=subscription_id
        )

    status = content['subscription']['status']
    if status in ('active', 'in_trial', 'non_renewing'):
        subscription.active = True
    else:
        subscription.active = False
    logger.info('[webhook] status=%s | set active to: %s' % (status,
        subscription.active))

    cancelled_at = int(content['subscription'].get('cancelled_at', 0))
    if cancelled_at > 0:
        logger.info('[webhook] subscription cancelled!')
        subscription.cancelled = True
    else:
        subscription.cancelled = False

    subscription.save()
    return HttpResponse() # Chargebee wants a 200 OK back
