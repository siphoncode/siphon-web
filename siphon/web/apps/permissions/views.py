
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import render

from siphon.web.utils import make_error
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.apps.models import App
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.apps.permissions import AppSharingException
from siphon.web.apps.apps.serializers import AppSerializer


class PermissionView(View):
    @method_decorator(login_required)
    def get(self, request):
        permission_type = request.GET.get('permission_type')
        app_id = request.GET.get('app_id')

        if permission_type != AppPermission.TYPE_BETA_TESTER:
            return make_error('Only the "%s" type is supported.' %
                AppPermission.TYPE_BETA_TESTER)

        # Check the App ID exists and is owned by the logged in user.
        try:
            app = App.objects.get(user=request.user, app_id=app_id)
        except App.DoesNotExist:
            return make_error('App does not exist, or you do not own ' \
                'this app.')

        beta_app = app.get_beta_testing_alias()
        serializer = AppSerializer(beta_app)
        shared_with = [{'username': user.username, 'email': user.email.lower()}
            for user in AppPermission.get_beta_testers(app)]

        return JsonResponse({
            'aliased_app': serializer.to_representation(beta_app),
            'shared_with': shared_with
        })

    @method_decorator(login_required)
    def post(self, request):
        permission_type = request.POST.get('permission_type')
        email = request.POST.get('email')
        app_id = request.POST.get('app_id')

        # Check the email address is a valid one.
        if not email:
            return make_error('Email address field is required.')
        try:
            validate_email(email)
        except ValidationError as e:
            return make_error('Invalid email address: %s' % e)

        # Check the App ID exists and is owned by the logged in user.
        try:
            app = App.objects.get(user=request.user, app_id=app_id)
        except App.DoesNotExist:
            return make_error('App does not exist, or you do not own ' \
                'this app.')

        # Make sure they have a valid paid subscription.
        pricing_url = 'https://getsiphon.com%s' % reverse('static:pricing')
        if not Subscription.user_has_valid_subscription(request.user):
            if permission_type == AppPermission.TYPE_BETA_TESTER:
                msg = 'Sorry, you need a paid subscription to share an app' \
                    ' with beta testers. Learn more here: %s' % pricing_url
            elif permission_type == AppPermission.TYPE_TEAM_MEMBER:
                msg = 'Sorry, you need a paid subscription to share an app' \
                    ' with your team. Learn more here: %s' % pricing_url
            else:
                raise RuntimeError('Unhandled: %s' % permission_type)
            return make_error(msg)

        # Make sure they have the right allowances in their subscription.
        subscription = Subscription.objects.get(user=request.user)
        if permission_type == AppPermission.TYPE_BETA_TESTER and \
        not subscription.plan.beta_tester_sharing:
            msg = 'Sorry, your paid subscription plan does not include beta ' \
                'testing. Learn more and upgrade here: %s' % pricing_url
            return make_error(msg)
        elif permission_type == AppPermission.TYPE_TEAM_MEMBER and \
        not subscription.plan.team_sharing:
            msg = 'Sorry, your paid subscription plan does not include team ' \
                'sharing. Learn more and upgrade here: %s' % pricing_url
            return make_error(msg)

        # Send the invite email.
        try:
            app_permission = AppPermission.create_and_send_invite(
                permission_type,
                app,
                email
            )
            return JsonResponse({'invite_code': app_permission.invite_code})
        except AppSharingException as e:
            return make_error(str(e))


class InvitationView(View):
    def _render(self, request, message=None, error=None):
        assert message is None or error is None
        status = 200
        context = {}
        if message:
            context['message'] = message
        elif error:
            context['error'] = error
            status = 400
        return render(request, 'accept-invite.html', context, status=status)

    @method_decorator(login_required)
    def get(self, request, invite_code):
        try:
            app_permission = AppPermission.objects.get(invite_code=invite_code)
            app = app_permission.app
        except AppPermission.DoesNotExist:
            return self._render(request, error='Unknown invite code.')

        # Sanity checks.
        if app_permission.deleted or app.deleted or \
        app_permission.permission_type not in \
        (AppPermission.TYPE_TEAM_MEMBER, AppPermission.TYPE_BETA_TESTER):
            return self._render(request, error='Sorry, this is an invalid ' \
                'or previously used invite code.')

        # If the model already has a user assigned (i.e. the invited email
        # address was already linked to a Siphon account) then make sure it
        # matches the authenticated user.
        if app_permission.user is not None and \
        app_permission.user != request.user:
            return self._render(request, error='Sorry, this team sharing ' \
                'invitation is linked to a different Siphon user account.')

        if request.user == app_permission.app.user:
            return self._render(request, error='You can not accept a ' \
                'team sharing invite to an app that you already own.')

        if app_permission.active is False:
            app_permission.activate(request.user)
        return self._render(request, message='You accepted the invitation ' \
            'to become a team member for "%s".' % app.name)
