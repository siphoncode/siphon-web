
from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.test_utils import (
    with_new_app,
    TEST_APP_NAME,
    TEST_USER_USERNAME,
    TEST_APP_ID
)

class TestAppDeletion(TestCase):
    def setUp(self):
        self.client = client.Client()
        # We need at least one bundler/streamer to be assigned to new apps
        Bundler(hostname='my.dummy.bundler').save()
        Streamer(hostname='my.dummy.streamer').save()
        BaseVersion(name='0.10', latest=True,
                    react_native_version='0.22.0').save()

    def _delete_app(self, app_id, user=None):
        if user is None:
            user = User.objects.get(username=TEST_USER_USERNAME)
        token = user.auth_token.key
        url = reverse('api:apps:apps', kwargs={'app_id': app_id})
        return self.client.delete(url, **{'X-Siphon-Token': token})

    @with_new_app
    def test_delete_app(self):
        """
        Test DELETE in the API and make sure the model is altered correctly.
        """
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)
        response = self._delete_app(TEST_APP_ID)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is True)

    @with_new_app
    def test_delete_app__unauthorized(self):
        """ Make sure user can't delete someone else's app. """
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)
        other_user = User.objects.create_user(
            'other_user',
            'other_user@getsiphon.com',
            'abc123aaa'
        )
        response = self._delete_app(TEST_APP_ID, user=other_user)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)

    @with_new_app
    def test_delete_app__already_deleted(self):
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)
        # Delete the app
        response = self._delete_app(TEST_APP_ID)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is True)
        # Delete again
        response = self._delete_app(TEST_APP_ID)
        self.assertEqual(response.status_code, 200)  # it should be idempotent
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is True)

    @with_new_app
    def test_delete_app__create_new_one_with_same_name(self):
        """
        Users should be able to create a brand new app re-using the name of
        a previously deleted app.
        """
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)
        # Delete the app
        response = self._delete_app(TEST_APP_ID)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is True)
        # Create a new one with the same name
        user = User.objects.get(username=TEST_USER_USERNAME)
        token = user.auth_token.key
        resp = self.client.post(reverse('api:apps:apps'),
            {'name': TEST_APP_NAME}, **{'X-Siphon-Token': token})
        print('C = %s' % resp.content)
        self.assertEqual(resp.status_code, 201)
        qs = App.objects.filter(name=TEST_APP_NAME)
        self.assertEqual(qs.count(), 2)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is True)
