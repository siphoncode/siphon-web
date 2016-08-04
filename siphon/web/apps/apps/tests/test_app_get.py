
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.apps.models import BaseVersion
from siphon.web.utils.test_utils import (
    with_new_app,
    TEST_USER_USERNAME,
    TEST_APP_ID
)

class TestGetIndividualApp(TestCase):
    def setUp(self):
        # We need at least one bundler so that it is assigned to new apps
        Bundler(hostname='my.dummy.bundler').save()
        Streamer(hostname='my.dummy.streamer').save()
        BaseVersion(name='0.10', latest=True,
                    react_native_version='0.22.0').save()
        self.client = client.Client()

    def _get_app(self, app_id, token=True):
        user = User.objects.get(username=TEST_USER_USERNAME)
        url = reverse('api:apps:apps', kwargs={'app_id': app_id})
        if token:
            return self.client.get(url,
                **{'X-Siphon-Token': user.auth_token.key})
        else:
            return self.client.get(url)
        return response

    @with_new_app
    def test_get_individual_app__valid(self):
        response = self._get_app(TEST_APP_ID, token=True)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content.decode('utf-8'))
        self.assertTrue(obj['id'] == TEST_APP_ID)

    @with_new_app
    def test_get_individual_app__does_not_exist(self):
        response = self._get_app('invalid-app-id', token=True)
        self.assertEqual(response.status_code, 404)

    @with_new_app
    def test_get_individual_app__unauthorized(self):
        response = self._get_app(TEST_APP_ID, token=False)
        self.assertEqual(response.status_code, 403)

    @with_new_app
    def test_post_individual_app_fails(self):
        """ Should not be able to do POST /apps/<id>. """
        user = User.objects.get(username=TEST_USER_USERNAME)
        token = user.auth_token.key
        url = reverse('api:apps:apps', kwargs={'app_id': TEST_APP_ID})
        response = self.client.post(url, **{'X-Siphon-Token': token})
        self.assertEqual(response.status_code, 405) # i.e. method not allowed
