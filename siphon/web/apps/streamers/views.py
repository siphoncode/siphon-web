
import random

from django.http import HttpResponse, JsonResponse
from siphon.web.apps.apps.models import App
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.permissions.models import AppPermission


def _error(error_type, message):
    return JsonResponse({'error_type': error_type, 'message': message},
        status=400)

def _make_response(app, stream_type):
    return JsonResponse({'streamer_url': app.get_streamer_url(stream_type)})

def streamers(request):
    if not request.user or not request.user.is_authenticated():
        return HttpResponse('Unauthorized', status=401)
    stream_type = request.GET.get('type')
    app_id = request.GET.get('app_id')
    if stream_type not in Streamer.STREAM_TYPES:
        return _error('error', 'Invalid stream type: %s' % stream_type)

    # Special case: wildcard notifications for the Siphon Sandbox app. In
    # this case we randomly pick a streamer.
    if app_id == '*':
        streamer = random.choice(Streamer.objects.all())
        streamer_url = streamer.get_signed_url(request.user.username,
            '*', stream_type)
        return JsonResponse({'streamer_url': streamer_url})

    try:
        app = App.objects.get(app_id=app_id)
    except App.DoesNotExist:
        return _error('error', 'Unknown app.')

    if app.is_beta_testing_alias() and app.user == request.user \
    and stream_type in (Streamer.STREAM_TYPE_LOG_WRITER,
    Streamer.STREAM_TYPE_NOTIFICATIONS):
        return _error('error', 'App owner can not stream logs and ' \
            'notifications for a beta testing alias app.')

    # The user must either (A) own the requested app or (B) is a member of a
    # valid team or (C) this is an alias and user is a beta tester.
    if app.user == request.user:
        return _make_response(app, stream_type)
    elif AppPermission.user_is_beta_tester(app, request.user):
        if stream_type == Streamer.STREAM_TYPE_LOG_READER:
            return _error('error', 'Sorry, you can not read logs from a ' \
                'a shared beta testing app that you do not own.')
        else:
            return _make_response(app, stream_type)
    else:
        aliased_app = AppPermission.get_team_member_alias(app, request.user)
        if aliased_app:
            if stream_type == Streamer.STREAM_TYPE_LOG_WRITER:
                return _error('error', 'Sorry, you can not write logs to ' \
                    'a shared team app.')
            else:
                return _make_response(aliased_app, stream_type)
        else:
            return _error('error', 'Unknown app.')
