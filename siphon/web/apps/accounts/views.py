
import json

from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as _login
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url

from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser

from siphon.web.utils import make_error
from siphon.web.apps.accounts import validate


def get_next_page(request):
    if 'next' in request.GET:
        next_page = request.GET['next']
        if is_safe_url(url=next_page, host=request.get_host()):
            return next_page
    return None


class RegisterView(View):
    def _render(self, request, params=None):
        if not params:
            params = {}
        return render(request, 'accounts/register.html', params)

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        from_landing = bool(request.GET.get('from_landing', False))
        from_tutorial = bool(request.GET.get('from_tutorial', False))

        try:
            validate.name(first_name, last_name)
            validate.email(email)
            validate.username(username)
            validate.password(password, confirm_value=password_confirm)
        except ValidationError as e:
            return self._render(request, {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'username': username,
                'error': ' '.join(e.messages)
            })

        # If we got this far, create the account and authenticate the user
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username
        )
        user.set_password(password)
        user.save()
        _login(request, authenticate(username=username, password=password))

        next_page = get_next_page(request)
        if from_landing:
            redirect_to = reverse('docs:quickstart')
        elif from_tutorial:
            redirect_to = reverse('docs:quickstart') + '#download-sandbox'
        elif next_page:
            redirect_to = next_page
        else:
            redirect_to = reverse('static:dashboard')

        # We need an interstitial redirect so that we can do mixpanel.alias()
        # at the correct time.
        return render(request, 'accounts/redirect.html', {
            'redirect_to': redirect_to
        })

    def get(self, request):
        return self._render(request)


class LoginView(View):
    def _render(self, request, username=None, error=None):
        params = {}
        if username:
            params['username'] = username
        if error:
            params['error'] = error
        register_url = reverse('accounts:register')
        next_page = get_next_page(request)
        if next_page:
            register_url += '?next=%s' % next_page
        params['register_url'] = register_url
        return render(request, 'accounts/login.html', params)

    def post(self, request):
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        if not username_or_email:
            return self._render(request, username=username_or_email,
                error='A username or email is required.')
        username_or_email = username_or_email.lower()
        try:
            if '@' in username_or_email:
                u = User.objects.get(email__iexact=username_or_email)
            else:
                u = User.objects.get(username__iexact=username_or_email)
        except User.DoesNotExist:
            return self._render(request, username=username_or_email,
                error='Unknown username or email.')

        user = authenticate(username=u.username, password=password)
        if user is None:
            return self._render(request, username=username_or_email,
                error='Unknown account or incorrect password.')
        elif not user.is_active:
            return self._render(request, username=username_or_email,
                error='This account is disabled.')

        # If we got this far, login the request
        _login(request, user)
        # If ?next is present and valid, redirect there, otherwise
        # we default to the dashboard.
        next_page = get_next_page(request)
        if next_page:
            return HttpResponseRedirect(next_page)
        else:
            return redirect('static:dashboard')

    def get(self, request):
        return self._render(request)


# Note: this view only applies to API-based logins.
@api_view(['POST'])
@parser_classes((JSONParser, FormParser))
def login(request):
    # User request.data with Rest parsers
    username = request.data.get('username')
    password = request.data.get('password')

    if not username:
        data = {'username': ['Username field is required.']}
        return Response(data, status=400, content_type='application/json')

    if not password:
        data = {'password': ['Password field is required.']}
        return Response(data, status=400, content_type='application/json')

    # Check if the username is an email address ('@' is restricted from being
    # included in a username)
    username = username.lower()
    if '@' in username:
        try:
            username = User.objects.get(email__iexact=username).username
        except User.DoesNotExist:
            data = {'username': ['Unknown or invalid email address.']}
            return Response(data, status=400, content_type='application/json')
    else:
        try:
            username = User.objects.get(username__iexact=username).username
        except User.DoesNotExist:
            data = {'username': ['Unknown or invalid username.']}
            return Response(data, status=400, content_type='application/json')

    user = authenticate(username=username, password=password)
    if user is not None:
        data = {'token': user.auth_token.key}
        response = Response(data, content_type='application/json')
    else:
        data = {'username': ['The username or password was incorrect.']}
        response = Response(data, status=400, content_type='application/json')
    return response

@api_view(['GET'])
def info(request):
    # Return 401 like we do for other API endpoints
    if not request.user or not request.user.is_authenticated():
        return make_error('Unauthorized.', status=401)

    subscription = None
    try:
        sub = request.user.paid_subscription
        subscription = {
            'plan_id': sub.plan.plan_id,
            'active': sub.active,
            'cancelled': sub.cancelled
        }
    except ObjectDoesNotExist:
        pass

    # For future-proofness with the free publishing plan, we'll also include
    # a flag to indicate whether a user has the ability to publish.
    can_publish = False
    if subscription and subscription['active'] is True:
        can_publish = True

    return HttpResponse(json.dumps({
        'username': request.user.username,
        'email': request.user.email,
        'subscription': subscription,
        'can_publish': can_publish
    }), content_type='application/json')
