
import json
import time
import os

from siphon.web.utils import make_error
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.submissions.models import Submission
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.apps.submissions.utils import validate_app, InvalidAppException

import requests
from django.core.mail import EmailMessage
from django.views.generic import View
from django.http import HttpResponse


def to_unix(dt):
    return time.mktime(dt.timetuple())

def email_app_snapshot(submission):
    app = submission.app
    bundler_url = app.bundler.get_signed_url(app.user.username,
        app.app_id, 'pull')
    # POST empty asset hashes so that it sends us everything back.
    headers = {'content-type': 'application/json'}
    resp = requests.post(bundler_url, headers=headers, data=json.dumps({
        'asset_hashes': {}
    }))
    zip_content = resp.content
    # Send the email
    email = EmailMessage(
        '[Siphon] New app submission!',
        'submission_id=%s\nuser=%s\n\nAPP:\n\n%s' % (submission.submission_id,
            app.user.username, str(app.__dict__)),
        'postmaster@getsiphon.com',
        ['james.potter@gmail.com', 'ali.roberts3@gmail.com']
    )
    email.attach('app.zip', zip_content, 'application/zip')
    email.send()


class SubmissionView(View):
    def post(self, request):
        if not request.user or not request.user.is_authenticated():
            return make_error('Not authorized.', status=401)
        elif not Subscription.user_has_valid_subscription(request.user):
            return make_error('You do not have an active subscription.')

        # if Submission.objects.filter(user=request.user).count() > 0:
            # return make_error('It looks like you already submitted an app to ' \
            #     'be published. If this is an error, or you would like to ' \
            #     'publish a different app, please email support: ' \
            #     'hello@getsiphon.com')

        # Check that the app exists and belongs to this user.
        app_id = request.POST.get('app_id')
        if not app_id:
            return make_error('Expecting "app_id" to be specified.')
        try:
            app = App.objects.get(app_id=app_id)
        except App.DoesNotExist:
            return make_error('Unknown app.')

        # Beta testing alias apps can not be published.
        if app.is_beta_testing_alias():
            return make_error('This app can not be published.')

        if app.user == request.user:
            if AppPermission.objects.filter(aliased_app=app).count() > 0:
                # This is an internal alias of a team app. Publishing is not
                # allowed by team members, in order to avoid confusion.
                return make_error('Sorry, a shared team app can only be ' \
                    'published by the team leader.')
        else:
            alias = AppPermission.get_team_member_alias(app, request.user)
            if alias:
                # This is a team app that has been shared with the
                # authenticated user. Only the team leader can publish.
                return make_error('Sorry, a shared team app can only be ' \
                    'published by the team leader.')
            else:
                # The user has no rights to this app at all.
                return make_error('Unknown app.')

        # If the user has one-or-more submissions for a *different* app
        # then fail. They can only publish one app at the moment.
        qs = Submission.objects.filter(user=request.user).exclude(app=app)
        if qs.count() > 0:
            return make_error('It looks like you already published ' \
                'another app. If this is an error, or you would ' \
                'like to publish a different app, please email support: ' \
                'hello@getsiphon.com')

        # Make sure that platform was given and is valid.
        platform = request.POST.get('platform')
        if not platform:
            return make_error('Expecting "platform" to be specified.')
        elif platform not in ('ios', 'android'):
            return make_error('The platform "%s" is not valid. Platform ' \
                'must be either "android" or "ios".')

        # Make sure base version associated with this app is not a
        # pre-release one.
        if app.base_version.id > BaseVersion.get_latest().id and \
        not app.base_version.latest:
            return make_error('The base version "%s" is not ' \
                'yet released.' % app.base_version.name)

        # If they already submitted this app before and it's still awaiting
        # build/approval (i.e. its not active, but it also didn't fail) then
        # don't allow them to submit again yet.
        latest = Submission.latest_submission_for_app(app, platform)
        if latest and (not latest.is_active and not latest.is_failed and \
                       latest.platform == platform):
            return make_error('This app is already in the publishing queue, ' \
                'or is waiting approval, so you can not publish an update ' \
                'yet. If this is an error, please contact support: ' \
                'hello@getsiphon.com')

        # Make sure that platform credentials were given
        hard_update = Submission.app_requires_hard_update(app, platform)
        platform_username = request.POST.get('platform_username')
        platform_password = request.POST.get('platform_password')
        if hard_update:
            if not platform_username or not platform_password:
                return make_error('Expecting "platform_username" and ' \
                    '"platform_password" for a hard update.')

        # Check that we have all the info we need to publish for the given
        # platform
        try:
            validate_app(app, platform)
        except InvalidAppException as e:
            return make_error(e.msg)

        # Generate a unique submission_id, but we won't store it in
        # the DB yet.
        submission_id = Submission.new_id()

        # Synchronously call the bundler to make a submission snapshot
        # with our new ID. It will keep an immutable record of the app's files
        # at this moment in time.
        submit_url = app.get_bundler_url_for_submission('submit',
            submission_id, platform=platform)
        if os.environ.get('SIPHON_ENV') != 'dev':
            resp = requests.post(submit_url,
                data={'submission_id': submission_id})
            if resp.status_code != 200:
                return make_error('Error making a snapshot of your app: "%s"' %
                    resp.content)

        # If all is fine so far, record the submission
        submission = Submission(
            submission_id=submission_id,
            app=app,
            user=request.user,
            base_version=app.base_version,
            display_name=app.display_name,
            platform=platform,
            platform_username=platform_username or '',
            platform_password=platform_password or ''
        )

        if hard_update:
            # For a hard update, the app needs a new binary before we
            # can activate this submission.
            submission.status = Submission.STATUS_PROCESSING

            # Temporary: email a snapshot to us. In future this is the point
            # where we will add this submission to the build queue.
            if os.environ.get('SIPHON_ENV') != 'dev':
                email_app_snapshot(submission)
        else:
            # For a soft update, we can mark the submission as active
            # right away because no new binary is needed.
            submission.status = Submission.STATUS_RELEASED
            submission.is_active = True
        submission.save()

        return HttpResponse(json.dumps({
            'id': submission.submission_id,
            'app_id': submission.app.app_id,
            'platform': submission.platform,
            'base_version': submission.base_version.name,
            'status': submission.status,
            'created': to_unix(submission.created),
            'last_updated': to_unix(submission.last_updated)
        }), content_type='application/json')


class CheckSubmissionView(View):
    def get(self, request):
        if not request.user or not request.user.is_authenticated():
            return make_error('Not authorized.', status=401)

        # Retrieve the app. It must be owned by the authenticated user
        # to continue.
        app_id = request.GET.get('app_id')
        platform = request.GET.get('platform')
        if not app_id:
            return make_error('App ID is required.')

        if not platform:
            return make_error('Platform is required.')

        try:
            app = App.objects.get(app_id=app_id)
        except App.DoesNotExist:
            return make_error('Unknown app or you do not own this app.')
        if app.user != request.user:
            return make_error('Unknown app or you do not own this app.')

        hard_update_required = \
            Submission.app_requires_hard_update(app, platform)
        return HttpResponse(json.dumps({
            'hard_update_required': hard_update_required
        }), content_type='application/json')

class ValidateAppView(View):
    def get(self, request):
        if not request.user or not request.user.is_authenticated():
            return make_error('Not authorized.', status=401)
        app_id = request.GET.get('app_id')
        platform = request.GET.get('platform')

        if not platform:
            return make_error('Expecting "platform" to be specified.')
        elif platform not in ('ios', 'android'):
            return make_error('The platform "%s" is not valid. Platform ' \
                'must be either "android" or "ios".')

        try:
            app = App.objects.get(app_id=app_id)
        except App.DoesNotExist:
            return make_error('Unknown app or you do not own this app.')
        if app.user != request.user:
            return make_error('Unknown app or you do not own this app.')

        try:
            validate_app(app, platform)
        except InvalidAppException as e:
            return make_error(e.msg)

        return HttpResponse(json.dumps({
            'status': 'ok'
        }), content_type='application/json')
