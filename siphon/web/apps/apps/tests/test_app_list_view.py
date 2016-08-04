
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.test_utils import (
    with_new_app,
    TEST_USER_USERNAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def _create_user():
    return User.objects.create_user(
        TEST_USER_USERNAME,
        TEST_USER_EMAIL,
        TEST_USER_PASSWORD
    )

class TestAppListView(TestCase):
    def setUp(self):
        # We need at least one bundler so that it is assigned to new apps
        Bundler(hostname='my.dummy.bundler').save()
        Streamer(hostname='my.dummy.streamer').save()
        BaseVersion(name='0.10', latest=True, react_native_version='0.22.2').save()
        self.client = client.Client()

    def test_get_user_apps__no_token(self):
        response = self.client.get(reverse('api:apps:apps'))
        self.assertEqual(response.status_code, 403)

    def test_get_user_apps__valid_token(self):
        user = _create_user()
        App.objects.create(user=user, name='app1')
        token = user.auth_token.key
        response = self.client.get(reverse('api:apps:apps'),
            **{'X-Siphon-Token': token})
        obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(obj, dict))

    @with_new_app
    def test_get_user_apps__invalid_token(self):
        response = self.client.get(reverse('api:apps:apps'),
            **{'X-Siphon-Token': 'badtoken'})
        obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 401)
        self.assertTrue('token' in obj)

    def test_get_user_apps__deleted(self):
        """ Deleted apps should not appear in the list. """
        user = _create_user()
        token = user.auth_token.key
        app1 = App.objects.create(user=user, name='app1')
        app2 = App.objects.create(user=user, name='app2')

        # First make sure they both appear
        response = self.client.get(reverse('api:apps:apps'),
            **{'X-Siphon-Token': token})
        obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(obj['results']), 2)

        # Now delete one, it should no longer appear
        app2.deleted = True
        app2.save()
        response = self.client.get(reverse('api:apps:apps'),
            **{'X-Siphon-Token': token})
        obj = json.loads(response.content.decode('utf-8'))
        apps = obj['results']
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0]['id'], app1.app_id)

    def test_get_user_apps__pagination(self):
        """
        Pagination should be disabled for apps list for now, until the
        dashboard supports it.
        """
        user = _create_user()
        token = user.auth_token.key
        for i in range(50):
            App.objects.create(user=user, name=str(i))
        response = self.client.get(reverse('api:apps:apps'),
            **{'X-Siphon-Token': token})
        obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(obj, dict))
        self.assertTrue('results' in obj)
        self.assertEqual(len(obj['results']), 50)
