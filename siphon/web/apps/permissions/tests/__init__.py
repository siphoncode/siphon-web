
import json

from django.contrib.auth.models import User
from django.test import client
from django.core.urlresolvers import reverse
from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart

from siphon.web.apps.permissions.models import AppPermission
from siphon.web.apps.subscriptions.models import Plan, Subscription
from siphon.web.utils.test_utils import (
    TEST_USER_USERNAME,
    TEST_USER_PASSWORD,
    TEST_APP_ID,
    TEST_APP_BASE_VERSION
)

OTHER_USER_USERNAME = 'another_user'
OTHER_USER_EMAIL = 'another_user@siphon.com'
OTHER_USER_PASSWORD = 'somepass1234'

SECOND_TESTER_USERNAME = 'second_beta_tester'
SECOND_TESTER_EMAIL = 'second_beta_tester@getsiphon.com'
SECOND_TESTER_PASSWORD = 'somepass12345'


def to_json(resp):
    s = resp.content.decode('utf-8')
    try:
        return json.loads(s)
    except ValueError:
        print('Can not decode JSON: "%s" [%s]' % (s, resp.status_code))
        raise

# Note: this is abstract, subclasses must also inherit TestCase.
class PermissionsTestCase(object):
    def setUp(self):
        self.client = client.Client()
        self.other_user = User.objects.create_user(OTHER_USER_USERNAME,
            OTHER_USER_EMAIL)
        self.other_user.set_password(OTHER_USER_PASSWORD)
        self.other_user.save()

        # Add another user for beta tester tests.
        self.second_tester = User.objects.create_user(SECOND_TESTER_USERNAME,
            SECOND_TESTER_EMAIL)
        self.second_tester.set_password(SECOND_TESTER_PASSWORD)
        self.second_tester.save()

        # Give our other user a valid subscription for publishing.
        plan = Plan.objects.create(
            name='A plan',
            plan_id='some-plan',
            interval='monthly',
            seats=1,
            monthly_active_users=1000,
            max_app_size=512,
            priority_support=False
        )
        Subscription.objects.create(
            user=self.other_user,
            plan=plan,
            active=True,
            cancelled=False,
            chargebee_id='test-chargebee-id'
        )

    def _login(self, username=TEST_USER_USERNAME, password=TEST_USER_PASSWORD):
        assert User.objects.filter(username=username).count() == 1
        self.client.login(
            username=username,
            password=password
        )

    def _login_as_other_user(self):
        assert User.objects.filter(username=OTHER_USER_USERNAME).count() == 1
        self.client.login(
            username=OTHER_USER_USERNAME,
            password=OTHER_USER_PASSWORD
        )

    def _share(self, permission_type, email, app_id=TEST_APP_ID):
        resp = self.client.post(reverse('api:permissions:permissions'), {
            'email': email,
            'app_id': app_id,
            'permission_type': permission_type
        })
        if resp.status_code == 302:
            obj = None
        else:
            obj = to_json(resp)
        return obj, resp.status_code

    def _accept(self, invite_code):
        url = reverse('permissions:accept-invite', kwargs={
            'invite_code': invite_code
        })
        return self.client.get(url)

    def _share_and_dont_accept(self):
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        self.assertEqual(status, 200, obj)
        invite_code = obj['invite_code']
        return AppPermission.objects.get(invite_code=invite_code)

    def _share_with_both_testers(self):
        testers = [
            (OTHER_USER_EMAIL, OTHER_USER_USERNAME,
                OTHER_USER_PASSWORD),
            (SECOND_TESTER_EMAIL, SECOND_TESTER_USERNAME,
                SECOND_TESTER_PASSWORD)
        ]
        perms = []
        for email, username, password in testers:
            self._login()  # Login as owner first.
            obj, status = self._share(self.permission_type, email)
            self.assertEqual(status, 200)
            invite_code = obj['invite_code']
            self.client.logout()
            self.client.login(
                username=username,
                password=password
            )
            resp = self._accept(invite_code)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(AppPermission.objects.filter(
                invite_code=invite_code, active=True).count(), 1)
            perms.append(AppPermission.objects.get(invite_code=invite_code))
        # Back to owner.
        self.client.logout()
        self._login()
        return perms

    def _get_sharing_status(self, permission=AppPermission.TYPE_BETA_TESTER):
        url = reverse('api:permissions:permissions') + '?app_id=' + \
            TEST_APP_ID + '&permission_type=' + permission
        resp = self.client.get(url)
        obj = to_json(resp)
        return obj, resp.status_code

    def _get_all_users(self):
        return (
            User.objects.get(username=TEST_USER_USERNAME),
            User.objects.get(username=OTHER_USER_USERNAME),
            User.objects.get(username=SECOND_TESTER_USERNAME)
        )

    def _development_pull(self, app_id):
        resp = self.client.get(reverse('api:bundlers:bundlers'), {
            'app_id': app_id,
            'base_version': TEST_APP_BASE_VERSION,
            'action': 'pull',
            'platform': 'ios'
        })
        obj = to_json(resp)
        return obj, resp.status_code

    def _delete(self, app_id):
        resp = self.client.delete(reverse('api:apps:apps', kwargs={
            'app_id': app_id
        }))
        try:
            obj = to_json(resp)
        except ValueError:
            obj = None
        return obj, resp.status_code

    def _put(self, app_id):
        url = reverse('api:apps:apps', kwargs={'app_id': app_id})
        params = {'base_version': TEST_APP_BASE_VERSION}
        # The django test client does a PUT with the wrong content-type
        # by default, so we fudge it here
        resp = self.client.put(url, data=encode_multipart(BOUNDARY, params),
            content_type=MULTIPART_CONTENT)
        try:
            obj = to_json(resp)
        except ValueError:
            if resp.status_code == 200:
                obj = None
            else:
                raise
        return obj, resp.status_code

    def _get_streamer_url(self, app_id, streamer_type):
        resp = self.client.get(reverse('api:streamers:streamers'), {
            'type': streamer_type,
            'app_id': app_id
        })
        obj = to_json(resp)
        return obj, resp.status_code

    def _share_and_accept(self):
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        invite_code = obj['invite_code']
        self._login_as_other_user()
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AppPermission.objects.filter(
            invite_code=invite_code, active=True).count(), 1)
        return AppPermission.objects.get(invite_code=invite_code)

    def _push(self, app_id):
        resp = self.client.get(reverse('api:bundlers:bundlers'), {
            'action': 'push',
            'app_id': app_id
        })
        obj = to_json(resp)
        return obj, resp.status_code

    def _publish(self, app_id):
        resp = self.client.post(reverse('api:submissions:submissions'), {
            'app_id': app_id,
            'platform': 'ios',
            'platform_username': 'dummy',
            'platform_password': 'dummy'
        })
        obj = to_json(resp)
        return obj, resp.status_code
