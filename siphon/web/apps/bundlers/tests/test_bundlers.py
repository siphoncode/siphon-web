
import json
import urllib
import base64
from decimal import Decimal
from urllib.parse import unquote

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.apps.submissions.models import Submission
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.utils.test_utils import (
    with_new_app,
    with_submission,
    TEST_APP_NAME,
    TEST_APP_ID,
    TEST_APP_BASE_VERSION,
    TEST_USER_USERNAME,
    TEST_USER_PASSWORD,
    TEST_USER_EMAIL,
    TEST_SUBMISSION_ID
)

def _to_dict(response):
    return json.loads(response.content.decode('utf-8'))

def _get_bundler_url(client, action, version=TEST_APP_BASE_VERSION,
                     platform=None):
    params = {
        'app_id': TEST_APP_ID,
        'action': action
    }
    if action == 'pull':
        params['base_version'] = version
        if platform:
            params['platform'] = platform
    response = client.get(reverse('api:bundlers:bundlers'), params)
    return _to_dict(response)


class TestBundler(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    @with_new_app
    def test_push__valid(self):
        """ Make sure a basic push works. """
        self._login()
        obj = _get_bundler_url(self.client, 'push')
        self.assertTrue('bundler_url' in obj)

    @with_new_app
    def test_pull__valid(self):
        """ Make sure that platform are handled correctly """
        self._login()
        obj_no_platform = _get_bundler_url(self.client, 'pull')
        self.assertTrue('bundler_url' in obj_no_platform)
        params = ['sumbmission_id=', 'platform=']
        self.assertTrue(not any([p in obj_no_platform['bundler_url'] \
                        for p in params]))
        obj_platform = _get_bundler_url(self.client, 'pull', platform='ios')
        self.assertTrue('bundler_url' in obj_platform)
        url = obj_platform['bundler_url']
        self.assertTrue('submission_id' not in url)
        self.assertTrue('platform' in url)

    @with_new_app
    def test_push__deleted_app(self):
        """ Should not be able to push to a deleted app. """
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertFalse(app.deleted)
        app.deleted = True
        app.save()
        obj = _get_bundler_url(self.client, 'push')
        self.assertEqual(obj['error_type'], 'app_deleted')
        self.assertTrue('bundler_url' not in obj)


class TestBundlerSubmissionPull(TestCase):
    """
    Tests for how production apps do a pull from the bundler, specificially
    by passing a `submission_id`. We use `submission_id a quick way to
    detect whether the device needs an update or not. No authentication
    should be required for this endpoint.

    We need to deal with the following cases:

    (A) There is a newer `submission_id` available for download and the
    `base_version` tied to that submission is the same as the one for the
    current submission that the device has, i.e. we are able to do an update.

    (B) There is a newer `submission_id` available but it is incompatible
    because the `base_version` does not match the one associated with the
    `submission_id` that the device currently has, i.e. their binary is
    out-of-date. In this case we should not show any error, but instead
    return the same response as (C).

    (C) The device is fully up-to-date and no new submissions are available,
    in which case it echoes back the given `submission_id`.
    """
    def setUp(self):
        self.client = client.Client()

    def _pull(self, current_submission_id):
        response = self.client.get(reverse('api:bundlers:bundlers'), {
            'current_submission_id': current_submission_id,
            'action': 'pull'
        })
        return response.status_code, _to_dict(response)

    def _make_newer(self, base_version=None, current=None, is_active=True,
    platform=None):
        if current is None:
            current = Submission.objects.get(submission_id=TEST_SUBMISSION_ID)
        if base_version is None:
            base_version = current.base_version
        if platform is None:
            platform = current.platform
        newer = Submission.objects.create(
            app=current.app,
            user=current.user,
            base_version=base_version,
            platform=platform,
            display_name=current.display_name,
            status='processing',
            is_active=is_active
        )
        newer.save()
        return newer

    @with_submission
    def test_pull__up_to_date(self):
        """ Case (C), no update is needed. """
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], TEST_SUBMISSION_ID)
        self.assertTrue('bundler_url' not in obj)

    @with_submission
    def test_pull__update_available(self):
        """ Case (A), a soft update is available. """
        # Create a newer submission that we should be upgraded to.
        newer = self._make_newer()
        # Do the pull, it should return an update
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], newer.submission_id)
        self.assertTrue('bundler_url' in obj)
        self.assertTrue(newer.submission_id in obj['bundler_url'])

    @with_submission
    def test_pull__incompatible_update_available(self):
        """
        Case (B), an update is available but this device's binary is not
        compatible (we refer to this as a hard update).
        """
        # Create a newer submission that has an imcompatible base_version
        # to the current submission
        x = Decimal(TEST_APP_BASE_VERSION) + Decimal('0.1')
        bv = BaseVersion.objects.create(name=str(x), latest=True,
                                        react_native_version='0.22.0')
        newer = self._make_newer(base_version=bv)
        # Do the pull, it should *not* return an update
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], TEST_SUBMISSION_ID)
        self.assertTrue('bundler_url' not in obj)

    @with_submission
    def test_pull__subscription_has_expired(self):
        """
        Case (D), the developer's subscription has expired so we
        disable all updates. We just echo back the given submission_id.
        """
        # Expire the test user's subscription
        user = User.objects.get(username=TEST_USER_USERNAME)
        subscription = Subscription.objects.get(user=user)
        subscription.active = False
        subscription.save()
        self.assertEqual(Subscription.user_has_valid_subscription(user), False)
        # Try to do a pull where usually we would get an update, but instead
        # we should get back our current submission_id
        self._make_newer()
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], TEST_SUBMISSION_ID)
        self.assertTrue('bundler_url' not in obj)

    @with_submission
    def test_pull__superuser_or_staff(self):
        """
        Sepcial case of (D), the developer account is marked as is_staff or
        is_superuser, so the subscription expiry limitation should not be
        enforced.
        """
        # Make a staff user
        staff_user = User.objects.create_user('mr_staff', 'a@b.com')
        staff_user.set_password('blablabla')
        staff_user.is_staff = True
        staff_user.save()
        # Make a staff app and corresponding submission, but don't give
        # the staff user an active subscription.
        app = App.objects.create(
            user=staff_user,
            name='my-staff-app',
            app_id='bla-bla-123',
            display_name='My Staff App'
        )
        app.save()
        current = Submission.objects.create(
            app=app,
            user=staff_user,
            base_version=BaseVersion.objects.get(name=TEST_APP_BASE_VERSION),
            display_name='My New App',
            status='processing',
            is_active=True,
            platform='ios'
        )
        current.save()
        # The staff user should have no active subscription
        self.assertEqual(Subscription.user_has_valid_subscription(staff_user),
            False)
        # When we do a pull it should try to update us to the newer
        # submission.
        newer = self._make_newer(current=current)
        status, obj = self._pull(current.submission_id)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], newer.submission_id)
        self.assertTrue('bundler_url' in obj)
        self.assertTrue(newer.submission_id in obj['bundler_url'])

    @with_submission
    def test_pull__newer_inactive_submission(self):
        """
        There are cases when a newer submission is available, i.e. the
        developer ran publish again, where the submission is not yet marked
        as active (for example, maybe its a hard update and still needs
        to go through the App Store approval queue).

        In these cases Django should not signal to the client that
        an upgrade is available, it should return the current submission ID.
        """
        # Create a newer submission that we should *not* be upgraded to.
        newer = self._make_newer(is_active=False)
        # Do the pull, it should return the current submission, not
        # the newer one.
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], TEST_SUBMISSION_ID)
        self.assertTrue('bundler_url' not in obj)

    @with_submission
    def test_pull__newer_submission_of_wrong_platform(self):
        """
        This tests for the case where an app tries to synchronise by doing a
        production pull, and a newer submission exists, but that submission
        is for a different platform.

        For example, if the developer has published a new version for iOS and
        an Android device is doing a production pull, Django should not
        return the "submission_id" for the newer iOS submission!
        """
        # Create a newer submission that we should *not* be upgraded to,
        # because it is for a different platform.
        newer = self._make_newer(is_active=True, platform='android')
        # Do the pull, it should return the current submission, not
        # the newer one.
        status, obj = self._pull(TEST_SUBMISSION_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['submission_id'], TEST_SUBMISSION_ID)
        self.assertTrue('bundler_url' not in obj)


class TestBundlerVersionManagement(TestCase):
    """
    Our siphon-base repository is tagged with versions e.g. v0.1, and these
    versions guarantee a particular version of React Native and set of
    wrappers that are available for a Siphon app to use.

    A Siphon app has a `Siphonfile` containing a "base_version" key, e.g. "0.1",
    and this version corresponds to a tag in the siphon-base repository.

    Note that when a user does `siphon push` we will need to update
    `App.base_version` to match the version stored in `Siphonfile`.

    When the /bundlers API is called with `action=pull` the caller must specify
    a `base_version` in the GET parameters to signal the version of the
    running app binary. This test suite ensures that Django does the right
    thing.
    """
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    def _get_pull_url(self, version):
        return _get_bundler_url(self.client, 'pull', version=version)

    @with_new_app
    def test_pull__same_version(self):
        """
        App's base_version == the app binary's base version:
        => everything is OK
        """
        self._login()
        obj = self._get_pull_url(TEST_APP_BASE_VERSION)
        self.assertTrue('bundler_url' in obj)

    @with_new_app
    def test_pull__app_binary_outdated(self):
        """
        App's base_version > the app binary's base version:
        => the app should be told that it needs an update
        """
        apps_base_version = Decimal(TEST_APP_BASE_VERSION)
        binary_base_version = apps_base_version - Decimal('0.2') # older

        self._login()
        obj = self._get_pull_url(str(binary_base_version))
        self.assertEqual(obj.get('error_type'), 'app_binary_outdated')
        self.assertTrue('message' in obj)
        self.assertFalse('bundler_url' in obj)

    @with_new_app
    def test_pull__app_binary_too_new(self):
        """
        App's base_version < the app binary's base version:
        => the app should be notified.

        Note: for production apps this can never happen, because the latest
        app bundle ships with the app when a user does `siphon publish`.
        But this can happen for Siphon Sandbox, in which case we nudge the user
        to update the "base_version" key in their Siphonfile.
        """
        apps_base_version = Decimal(TEST_APP_BASE_VERSION)
        binary_base_version = apps_base_version + Decimal('0.2') # newer

        self._login()
        obj = self._get_pull_url(str(binary_base_version))
        self.assertEqual(obj.get('error_type'), 'app_binary_too_new')
        self.assertTrue('message' in obj)
        self.assertFalse('bundler_url' in obj)


class TestBundlerSecurity(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    @with_new_app
    def test_authentication(self):
        """ Should not be able to get bundler URL for another user's app. """
        other_user = User.objects.create_user(
            username='other_user',
            email='other@user.com'
        )
        other_user.set_password('bananas')
        other_user.save()
        self.client.login(username='other_user', password='bananas')
        for action in ('push', 'pull'):
            obj = _get_bundler_url(self.client, action)
            self.assertEqual(obj['message'], 'Unknown app.')

    @with_new_app
    def test_https(self):
        """
        When doing a push/pull, we should always be given an https:// URL for
        the bundler server.
        """
        self._login()
        for action in ('push', 'pull'):
            obj = _get_bundler_url(self.client, action)
            self.assertTrue('bundler_url' in obj)
            self.assertTrue(obj['bundler_url'].startswith('https://'))

    @with_submission
    def test_production_handshake(self):
        # We need a newer submission to exist so that we're given
        # a bundler_url to upgrade with
        current = Submission.objects.get(submission_id=TEST_SUBMISSION_ID)
        latest = Submission.objects.create(
            app=current.app,
            user=current.user,
            base_version=current.base_version,
            display_name=current.display_name,
            platform=current.platform,
            status='processing',
            is_active=True
        )
        # Get the bundler_url and unpack its GET parameters
        response = self.client.get(reverse('api:bundlers:bundlers'), {
            'current_submission_id': TEST_SUBMISSION_ID,
            'action': 'pull'
        })
        bundler_url = _to_dict(response)['bundler_url']
        params = {}
        for part in urllib.parse.urlsplit(bundler_url).query.split('&'):
            k, v = part.split('=')
            params[k] = v
        # Ensure that the JSON contains what we're expecting
        t = unquote(params['handshake_token'])
        token = base64.b64decode(t).decode('utf8')
        obj = json.loads(token)
        self.assertEqual(obj['submission_id'], latest.submission_id)

    @with_new_app
    def test_development_handshake(self):
        # Get the bundler_url and unpack its GET parameters
        self._login()
        bundler_url = _get_bundler_url(self.client, 'push')['bundler_url']
        params = {}
        for part in urllib.parse.urlsplit(bundler_url).query.split('&'):
            k, v = part.split('=')
            params[k] = v

        # Ensure that the JSON contains what we're expecting
        t = unquote(params['handshake_token'])
        token = base64.b64decode(t).decode('utf8')
        obj = json.loads(token)
        self.assertEqual(obj['app_id'], TEST_APP_ID)
        self.assertEqual(obj['user_id'], TEST_USER_USERNAME)
