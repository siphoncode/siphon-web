
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.accounts.models import Token, Invitation
from siphon.web.apps.accounts import validate
from siphon.web.utils.test_utils import (
    with_new_user,
    with_new_subscribed_user,
    TEST_USER_USERNAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
    TEST_PLAN_ID
)


class TestAccountInfo(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    @with_new_user
    def test_get_info__no_subscription(self):
        self._login()
        response = self.client.get(reverse('api:accounts:info'))
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content.decode('utf-8'))
        data = {
            'subscription': None,
            'email': TEST_USER_EMAIL,
            'username': TEST_USER_USERNAME,
            'can_publish': False
        }
        for k, v in data.items():
            self.assertEqual(obj[k], v)

    @with_new_subscribed_user
    def test_get_info__with_subscription(self):
        self._login()
        response = self.client.get(reverse('api:accounts:info'))
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(obj['can_publish'], True)
        self.assertEqual(obj['subscription']['plan_id'], TEST_PLAN_ID)
        self.assertEqual(obj['subscription']['active'], True)
        self.assertEqual(obj['subscription']['cancelled'], False)

    @with_new_user
    def test_get_info__not_authenticated(self):
        response = self.client.get(reverse('api:accounts:info'))
        self.assertEqual(response.status_code, 401)
        obj = json.loads(response.content.decode('utf-8'))
        self.assertTrue('detail' in obj)


class TestTokenModel(TestCase):
    def test_token_creation(self):
        # User creation results in the generation of a token (accessed by
        # reverse lookup)
        user = User.objects.create_user(
            TEST_USER_USERNAME,
            TEST_USER_EMAIL,
            TEST_USER_PASSWORD
        )
        self.assertTrue(isinstance(user.auth_token, Token))


class TestRegistrationView(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _register(self, params=None):
        data = {
            'first_name': 'Dogend',
            'last_name': 'Jenkins',
            'username': TEST_USER_USERNAME,
            'email': TEST_USER_EMAIL,
            'password': TEST_USER_PASSWORD,
            'password_confirm': TEST_USER_PASSWORD
        }
        data.update(params or {})
        url = reverse('accounts:register')
        response = self.client.post(url, data)
        return response.content.decode('utf-8'), response

    def test_registration__valid(self):
        content, response = self._register()
        self.assertEqual(response.status_code, 200)

        # We're expecting to get the interstitial redirect page that
        # we go to after registration for mixpanel.alias()
        url = reverse('static:dashboard')
        meta_tag = '<meta http-equiv="refresh" content="2;url=%s">' % url
        self.assertTrue(meta_tag in content)

        # Manually follow the redirect and make sure we're logged in OK.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_registration__missing_username(self):
        content, response = self._register(params={'username': ''})
        self.assertTrue(validate.MSG_USERNAME_REQUIRED in content)

    @with_new_user
    def test_registration__duplicate_username(self):
        content, response = self._register(params={
            'email': 'different@email.com'
        })
        self.assertTrue(validate.MSG_USERNAME_TAKEN in content)

    @with_new_user
    def test_registration__duplicate_email(self):
        content, response = self._register(params={
            'username': 'differentuser',
            'email': TEST_USER_EMAIL
        })
        self.assertTrue(validate.MSG_EMAIL_TAKEN in content)

    def test_registration__bad_username(self):
        content, response = self._register(params={
            'username': 'fkaksdfjSDFA@5345'
        })
        self.assertTrue(validate.MSG_USERNAME_INVALID in content)

    def test_registration__bad_password(self):
        content, response = self._register(params={'password': 'a3'})
        self.assertTrue(validate.MSG_PASSWORD_INVALID in content)


class TestAPILogin(TestCase):
    @with_new_user
    def setUp(self):
        self.client = client.Client()

    def _login(self, params):
        response = self.client.post(
            reverse('api:accounts:login'),
            data=json.dumps(params),
            content_type='application/json'
        )
        return response, json.loads(response.content.decode('utf-8'))

    def test_login(self):
        response, obj = self._login({
            'username': TEST_USER_USERNAME,
            'password': TEST_USER_PASSWORD
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('token' in obj)

    def test_login__with_email(self):
        response, obj = self._login({
            'username': TEST_USER_EMAIL,
            'password': TEST_USER_PASSWORD
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue('token' in obj)

    def test_login__bad_username(self):
        response, obj = self._login({
            'username': 'NotAUser123',
            'password': TEST_USER_PASSWORD
        })
        self.assertEqual(response.status_code, 400)
        self.assertTrue('username' in obj)

    def test_login__bad_email(self):
        response, obj = self._login({
            'username': 'bad@email.com',
            'password': TEST_USER_PASSWORD
        })
        self.assertEqual(response.status_code, 400)
        self.assertTrue('username' in obj)

    def test_login__bad_password(self):
        response, obj = self._login({
            'username': TEST_USER_USERNAME,
            'password': 'badpassword'
        })
        self.assertEqual(response.status_code, 400)
        self.assertTrue('username' in obj)
