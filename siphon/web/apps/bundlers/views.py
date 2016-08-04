
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse, JsonResponse
from django.conf import settings

from siphon.web.apps.apps.models import App
from siphon.web.apps.submissions.models import Submission
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.permissions.models import AppPermission


def _error(error_type, message):
    return JsonResponse({'error_type': error_type, 'message': message},
        status=400)

def _handle_development_pull(request):
    # Retrieve the app
    app_id = request.GET.get('app_id')
    try:
        app = App.objects.get(app_id=app_id, deleted=False)
    except App.DoesNotExist:
        return _error('error', 'Unknown app.')
    is_beta_testing_alias = app.is_beta_testing_alias()

    if app.user == request.user:
        if is_beta_testing_alias:
            return _error('error',
                'App owner can not pull a beta testing app.')
    elif request.user.username == settings.SIPHON_BACKDOOR_USER:
        pass  # allowed.
    elif not AppPermission.user_is_beta_tester(app, request.user):
        # Only beta testers can pull an app that isn't theirs.
        return _error('error', 'Unknown app.')

    if is_beta_testing_alias and app.master_app.deleted:
        return _error('error', 'You can no longer pull this beta app because' \
            ' it was deleted.')

    # Check the given base_version
    try:
        base_version = Decimal(request.GET.get('base_version'))
    except (InvalidOperation, TypeError):
        return _error('error', 'Invalid base_version format.')

    platform = request.GET.get('platform')

    # Version compatibility check
    app_version = Decimal(app.base_version.name)
    binary_version = Decimal(base_version)
    if app_version == binary_version:
        bundler_url = app.get_bundler_url('pull', platform)
        return JsonResponse({'bundler_url': bundler_url})
    elif app_version > binary_version:
        return _error('app_binary_outdated', 'App binary is outdated.')
    else:
        return _error('app_binary_too_new', 'App binary is too new.')

def _handle_production_pull(request):
    """ Refer to the doc 'Polling updates in apps' for context. """
    # Check the submission_id that the client passed to us exists.
    current_submission_id = request.GET.get('current_submission_id')
    try:
        current = Submission.objects.get(submission_id=current_submission_id)
    except Submission.DoesNotExist:
        return _error('error', 'Unknown submission ID: %s' %
            current_submission_id)

    # See if there are any newer submissions for this app.
    latest = current.get_latest_active()

    # Handle the special case where the developer's subscription has
    # expired. In this case we simply echo back the submission_id that the
    # client gave us. Effectively we just disable updates but don't throw any
    # errors back to the client.
    user = current.user
    if not Subscription.user_has_valid_subscription(user):
        # Note: staff and superusers are exempt from this check.
        if not (user.is_staff or user.is_superuser):
            return JsonResponse({'submission_id': current.submission_id})

    if latest is None or latest == current:
        # Case (C), the client is fully up-to-date, so we just echo back the
        # the submission_id that the client gave us and nothing happens.
        obj = {'submission_id': current.submission_id}
    elif latest.created >= current.created:
        a, b = (Decimal(sub.base_version.name) for sub in (latest, current))
        if a == b:
            # Case (A), there is an update available and the client is
            # prepared for it because it has the same base_version.
            bundler_url = latest.app.get_bundler_url_for_submission('pull',
                latest.submission_id)
            obj = {
                'submission_id': latest.submission_id,
                'bundler_url': bundler_url
            }
        else:
            # Case (B), there is an update available but the client's binary
            # is not prepared for it because it has a different base_version.
            # We just echo back the submission_id that the client gave us.
            obj = {'submission_id': current.submission_id}
    else:
        # This should never happen, so we'll throw a 500 so that Django
        # will email us in case it ever does.
        raise RuntimeError('Unexpected state: %s, %s' % (current, latest))
    return JsonResponse(obj)

def _handle_push(request):
    # Retrieve the app
    app_id = request.GET.get('app_id')
    try:
        app = App.objects.get(app_id=app_id)
    except App.DoesNotExist:
        return _error('error', 'Unknown app.')

    if app.deleted:
        return _error('app_deleted', 'You can not push to a deleted app.')

    # Deal with internally aliased team shared apps.
    if app.user != request.user:
        app = AppPermission.get_team_member_alias(app, request.user)
        if not app:
            return _error('error', 'Unknown app.')

    return JsonResponse({'bundler_url': app.get_bundler_url('push')})

def bundlers(request):
    action = request.GET.get('action')

    # Production pull does not require authentication
    if action == 'pull' and 'current_submission_id' in request.GET:
        return _handle_production_pull(request)

    # All other actions require authentication
    if not request.user or not request.user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)

    if action == 'push':
        return _handle_push(request)
    elif action == 'pull' and 'app_id' in request.GET:
        return _handle_development_pull(request)
    else:
        return _error('error', 'Invalid action.')
