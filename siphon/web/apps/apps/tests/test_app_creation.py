
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.test_utils import (
    TEST_APP_NAME,
    TEST_USER_USERNAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD
)

class TestAppCreation(TestCase):
    def setUp(self):
        self.client = client.Client()
        # We need at least one bundler/streeamer to be assigned to new apps
        Bundler(hostname='my.dummy.bundler').save()
        Streamer(hostname='my.dummy.streamer').save()
        BaseVersion(name='0.10', latest=True,
                    react_native_version='0.22.2').save()
        BaseVersion(name='0.11', latest=False,
                    react_native_version='0.26.0').save()
        self.user = User.objects.create_user(
            TEST_USER_USERNAME,
            TEST_USER_EMAIL,
            TEST_USER_PASSWORD
        )

    def _create_app(self, app_name, user=None):
        if user is None:
            user = self.user
        token = user.auth_token.key
        return self.client.post(reverse('api:apps:apps'), {'name': app_name},
            **{'X-Siphon-Token': token})

    def test_app_model_creation(self):
        # Should generate a new key on creation
        app = App.objects.create(user=self.user, name=TEST_APP_NAME)
        self.assertTrue(app.app_id is not None)

    def test_duplicate_app_name__different_users(self):
        """
        Distinct users *should* be able to create apps that have the same name.
        """
        name = 'valid-dupe-name'
        response = self._create_app(name, user=self.user)
        self.assertEqual(response.status_code, 201)
        apps = App.objects.filter(name=name)
        self.assertEqual(apps.count(), 1)

        other_user = User.objects.create_user(
            'other_user', 'some@email.com', 'some_password'
        )
        response = self._create_app(name, user=other_user)
        self.assertEqual(response.status_code, 201)
        apps = App.objects.filter(name=name)
        self.assertEqual(apps.count(), 2)
        self.assertNotEqual(apps[0].app_id, apps[1].app_id)

    def test_duplicate_app_name__same_user(self):
        """
        A single user should not be able to create two apps with the same name.
        """
        name = 'my-app-name'

        response = self._create_app(name)
        self.assertEqual(response.status_code, 201)
        n = App.objects.filter(name=name, user=self.user).count()
        self.assertEqual(n, 1)

        # This should fail
        response = self._create_app(name)
        self.assertEqual(response.status_code, 400)
        apps = App.objects.filter(name=name, user=self.user)
        # There should only be one App belonging to the user here
        self.assertEqual(apps.count(), 1)

    def test_create_app_with_api(self):
        name = 'valid-app-name_123'  # all of the allowed characters
        response = self._create_app(name)
        self.assertEqual(response.status_code, 201)
        obj = json.loads(response.content.decode('utf-8'))
        # Check all keys are present in response
        keys = ('name', 'id', 'created', 'last_updated', 'published')
        self.assertTrue(all(key in obj for key in keys))

    def test_create_app_with_api__bad_names(self):
        for name in ('', 'bad$$$name', 'reallylong' * 5000, '應用', 'Ansökan'):
            response = self._create_app(name)
            self.assertEqual(response.status_code, 400,
                             'Name should cause error: "%s"' % name)
            obj = json.loads(response.content.decode('utf-8'))
            self.assertTrue('name' in obj)
            self.assertEqual(len(obj), 1)

    def test_create_app__assigns_bundler(self):
        """ A random bundler should be assigned when an app is created. """
        name = 'my-new-app'
        response = self._create_app(name)
        self.assertEqual(response.status_code, 201)
        app = App.objects.filter(name=name).first()
        self.assertTrue(isinstance(app.bundler, Bundler))

    def test_create_app__assigns_streamer(self):
        """ A random streamer should be assigned when an app is created. """
        name = 'my-new-app'
        response = self._create_app(name)
        self.assertEqual(response.status_code, 201)
        app = App.objects.filter(name=name).first()
        self.assertTrue(isinstance(app.streamer, Streamer))

    def test_create_app__assigns_base_version(self):
        """ A random streamer should be assigned when an app is created. """
        name = 'my-new-app'
        response = self._create_app(name)
        self.assertEqual(response.status_code, 201)
        app = App.objects.filter(name=name).first()
        self.assertTrue(isinstance(app.base_version, BaseVersion))
        self.assertEqual(app.base_version.latest, True)
