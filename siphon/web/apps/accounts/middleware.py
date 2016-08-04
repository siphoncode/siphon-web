
import json
from django.http import HttpResponse
from django.contrib.auth.models import User

from siphon.web.apps.accounts.models import Token
from siphon.web.apps.apps.models import App
from siphon.web.utils.external import verify_handshake, HandshakeError


def get_header(request, name):
    # Django converts headers of the form X-Header to HTTP_X_HEADER
    # except for requests from the test client (weird).
    token = request.META.get(name)
    if not token:
        alt_name = 'HTTP_%s' % name.replace('-', '_').upper()
        token = request.META.get(alt_name)
    return token

def make_401_response(message):
    data = {'token': [message]}
    return HttpResponse(json.dumps(data), status=401,
        content_type='application/json')

def clean_encoding(s):
    """
    Make sure the given url-encoded string matches the exact format that
    Python uses, in particular python encodes spaces as `%20` but Go encodes
    as `+` and that causes the handshake auth to fail.
    """
    return s.replace('+', '%20')


class TokenAuthMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_anonymous():
            return None  # user is already logged-in, don't do anything else
        token = get_header(request, 'X-Siphon-Token')
        if token:
            try:
                token_object = Token.objects.get(key=token)
                # If we got this far, "login" the user but skip session stuff
                request.user = token_object.user
                # Hack so that CSRF isn't enforced for token auth
                request.csrf_processing_done = True
            except Token.DoesNotExist:
                return make_401_response('Bad access token.')
        return None


class HandshakeAuthMiddleware(object):
    """
    For a small subset of API endpoints we allow authentication via the
    X-Siphon-Handshake-Token/X-Siphon-Handshake-Signature headers, so that
    the bundler can authenticate.
    """
    def is_handshake_endpoint(self, request):
        # get_full_path() looks like this: '/api/v1/apps/<app-id>'
        path = request.get_full_path()
        if path.startswith('/api/v1/apps/') and request.method == 'PUT':
            return True
        else:
            return False

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_anonymous():
            return None  # user is already logged-in, don't do anything else
        elif not self.is_handshake_endpoint(request):
            return None  # ignore endpoints for which we don't allow this
        elif 'app_id' not in view_kwargs:
            return None
        token = get_header(request, 'X-Siphon-Handshake-Token')
        signature = get_header(request, 'X-Siphon-Handshake-Signature')
        if token and signature:
            try:
                # Clean up the headers
                token = clean_encoding(token)
                signature = clean_encoding(signature)
                # Verify (note: must be a "push" action as the token/signature
                # are passed through from the user's push).
                username, app_id = verify_handshake(token, signature, 'push')
                user = User.objects.get(username=username)
                app = App.objects.get(app_id=app_id)
                if app.user != user or app_id != view_kwargs['app_id']:
                    return make_401_response('Not authorized.')
                request.user = user
                # Hack so that CSRF isn't enforced for token auth
                request.csrf_processing_done = True
            except (HandshakeError, App.DoesNotExist, User.DoesNotExist):
                return None
        return None
