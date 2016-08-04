import json
from copy import deepcopy

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.test_utils import (
    TEST_APP_NAME,
    TEST_USER_USERNAME,
    TEST_USER_EMAIL,
    TEST_APP_ID,
    TEST_FACEBOOK_APP_ID,
    TEST_APP_ICON_IOS,
    TEST_APP_ICON_ANDROID
)

class TestAppModification(TestCase):
    """
    These are tests for the PUT /apps/<id> endpoint. It's used by the bundler
    to update `App.display_name`, `App.facebook_app_id` and `App.base_version`,
    `App.app_store_name`, `App.play_store_name`, `App.app_store_language`,
    `App.play_store_language`.
    """
    def setUp(self):
        self.client = client.Client()
        # We need at least one bundler/streamer to be assigned to new apps
        Bundler(hostname='my.dummy.bundler').save()
        Streamer(hostname='my.dummy.streamer').save()
        # This will be assigned to our app by default
        self.base1 = BaseVersion(name='0.10', latest=True,
                                 react_native_version='0.22.2')
        self.base1.save()
        # This one should not be but we will switch to it
        self.base2 = BaseVersion(name='0.11', react_native_version='0.26.0')
        self.base2.save()
        # Make our user and test app
        user = User.objects.create_user(TEST_USER_USERNAME, TEST_USER_EMAIL)
        App.objects.create(user=user, name=TEST_APP_NAME, app_id=TEST_APP_ID)

    def _put(self, app_id, params, user=None, headers=None):
        assert user is None or headers is None  # can't be both
        if headers is None:
            user = User.objects.get(username=TEST_USER_USERNAME)
            token = user.auth_token.key
            headers = {'X-Siphon-Token': token}
        url = reverse('api:apps:apps', kwargs={'app_id': app_id})
        # The django test client does a PUT with the wrong content-type
        # by default, so we fudge it here
        from django.test.client import MULTIPART_CONTENT, BOUNDARY, \
            encode_multipart
        return self.client.put(
            url,
            data=encode_multipart(BOUNDARY, params),
            content_type=MULTIPART_CONTENT,
            **headers
        )

    def _get_handshake_headers(self, username=TEST_USER_USERNAME):
        from siphon.web.utils.external import make_development_handshake
        token, signature = make_development_handshake('push',
            username, TEST_APP_ID)
        return {
            'X-Siphon-Handshake-Token': token,
            'X-Siphon-Handshake-Signature': signature
        }

    def test_change_base_version(self):
        # Make sure default base_version assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID, {'base_version': self.base2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base2.name
        )

    def test_change_base_version__bumps_last_updated(self):
        """ App.last_updated should be bumped by the PUT. """
        # Make sure default base_version assigned as expected and remember the
        # current value of App.last_updated
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.base_version.name, self.base1.name)
        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID, {'base_version': self.base2.name})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.base_version.name, self.base2.name)
        self.assertTrue(app.last_updated > current_last_updated)

    def test_change_base_version__unknown_version(self):
        """
        Switching the base_version should fail if the new base_version
        doesn't exist in our database.
        """
        # Make sure default base_version assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        # Now try to change it to a non-existent base_version
        response = self._put(TEST_APP_ID, {'base_version': '0.8'})
        self.assertEqual(response.status_code, 400)
        # The change should not have been made
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )

    def test_change_base_version__with_valid_handshake_but_unknown_app(self):
        """
        Switching the base_version should fail gracefully if the given app
        does not exist in the database even though the handshake is valid.
        """
        headers = self._get_handshake_headers()
        # Make sure default base_version assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        # Try to legitimately PUT as the bundler would but with the
        # wrong app_id
        response = self._put('unknown-app', {'base_version': self.base2.name},
            headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name  # should not have changed!
        )

    def test_change__with_handshake(self):
        """
        Check that authentication with X-Siphon-Handshake-Token and
        X-Siphon-Handshake-Signature is enabled for PUT /apps/<id>.
        These are used by the bundler to authenticate but *only* for this
        exact endpoint.
        """
        headers = self._get_handshake_headers()
        # Make sure default values assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Try to legitimately PUT as the bundler would
        params = {'base_version': self.base2.name, 'display_name': 'New Name'}
        response = self._put(TEST_APP_ID, params, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base2.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name,
            'New Name')

    def test_change__with_bad_handshake(self):
        """ Make sure it fails when using e.g. another user's handshake. """
        bad_user = User.objects.create_user('bad', 'a@b.com', 'idjfisjdf3aa')
        bad_headers = self._get_handshake_headers(username=bad_user.username)
        # Make sure default base_version assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Now try to do a PUT with the wrong handshake
        params = {'base_version': self.base2.name, 'display_name': 'New Name'}
        response = self._put(TEST_APP_ID, params, headers=bad_headers)
        self.assertEqual(response.status_code, 401)
        # Model should not have changed
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')

    def test_handshake_auth_only_works_for_PUT(self):
        """ Handshake authentication should not work for e.g. GET. """
        headers = self._get_handshake_headers()
        url = reverse('api:apps:apps', kwargs={'app_id': TEST_APP_ID})
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 403)

    def test_handshake_auth_only_works_for_apps_endpoint(self):
        """
        Handshake authentication should not work for other endpoints at all.
        """
        # We're going to try to do GET /bundlers with the correct user's
        # handshake headers.
        headers = self._get_handshake_headers()
        params = {'app_id': TEST_APP_ID, 'action': 'push'}
        response = self.client.get(reverse('api:bundlers:bundlers'),
            params, **headers)
        self.assertEqual(response.status_code, 401)

    def test_change__unauthorized(self):
        # Make sure default values assigned as expected
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Now try to change it without authenticating at all
        params = {'base_version': self.base2.name, 'display_name': 'New Name'}
        response = self._put(TEST_APP_ID,
                             params, headers={})  # no auth headers
        self.assertEqual(response.status_code, 403)
        # Model should not have changed
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).base_version.name,
            self.base1.name
        )
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')

    def test_change_display_name(self):
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID, {'display_name': 'Test App'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).display_name,
            'Test App'
        )

    def test_change_display_name__too_long(self):
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        bad_name = 'Long' * 40
        response = self._put(TEST_APP_ID, {'display_name': bad_name})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')

    def test_change_display_name__bumps_last_updated(self):
        """ App.last_updated should be bumped by the PUT. """
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.display_name, '')
        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID, {'display_name': 'New Name'})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.display_name, 'New Name')
        self.assertTrue(app.last_updated > current_last_updated)

    def test_change_display_name__exotic_characters(self):
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Now change it and check that the model reflects our change
        for name in ('應用', '应用', 'Ansökan'):
            response = self._put(TEST_APP_ID, {'display_name': name})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                App.objects.get(app_id=TEST_APP_ID).display_name,
                name
            )

    def test_change_facebook_app_id(self):
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                            {'facebook_app_id': TEST_FACEBOOK_APP_ID})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).facebook_app_id,
            TEST_FACEBOOK_APP_ID
        )

    def test_change_facebook_app_id__too_long(self):
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).display_name, '')
        bad_name = 'Long' * 40
        response = self._put(TEST_APP_ID, {'facebook_app_id': bad_name})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).facebook_app_id,
                        '')

    def test_change_facebook_app_id__bumps_last_updated(self):
        """ App.last_updated should be bumped by the PUT. """
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.facebook_app_id, '')
        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                        {'facebook_app_id': TEST_FACEBOOK_APP_ID})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.facebook_app_id,
                         TEST_FACEBOOK_APP_ID)
        self.assertTrue(app.last_updated > current_last_updated)

    def test_change_store_language(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        response = self._put(TEST_APP_ID, {'app_store_language': 'en',
                                           'play_store_language': 'ky-KG'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).app_store_language,
            'en'
        )
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).play_store_language,
            'ky-KG'.lower()
        )

    def test_change_store_language_no_language(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        response = self._put(TEST_APP_ID, {'app_store_language': '',
                                           'play_store_language': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).app_store_language,
            ''
        )
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).play_store_language,
            ''
        )

    def test_change_store_languages__invalid_language_code(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        response = self._put(TEST_APP_ID, {'app_store_language': 'NOT_CODE',
                                           'play_store_language': 'ky-KG'})

        self.assertEqual(response.status_code, 400)
        response = self._put(TEST_APP_ID, {'app_store_language': 'en',
                                           'play_store_language': 'NOT_CODE'})

        self.assertEqual(response.status_code, 400)

        self.assertEqual(response.status_code, 400)
        response = self._put(TEST_APP_ID, {'app_store_language': 'no-CO',
                                           'play_store_language': 'ky-KG'})
        self.assertEqual(response.status_code, 400)
        response = self._put(TEST_APP_ID, {'app_store_language': 'en',
                                           'play_store_language': 'no-CO'})

        self.assertEqual(response.status_code, 400)

        # If any one of the fields is invalid, don't update the app model
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).app_store_language,
            App.objects.get(app_id=TEST_APP_ID).play_store_language, '')

    def test_change_store_language__bumps_last_updated(self):
        """ App.last_updated should be bumped by the PUT. """
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                        {'app_store_language': 'en'})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, 'en'.lower())
        self.assertTrue(app.last_updated > current_last_updated)

        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                        {'play_store_language': 'Af'})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.play_store_language, 'Af'.lower())
        self.assertTrue(app.last_updated > current_last_updated)

    def test_change_store_name(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                            {'app_store_name': TEST_APP_NAME,
                             'play_store_name': TEST_APP_NAME})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).app_store_name,
            App.objects.get(app_id=TEST_APP_ID).play_store_name,
            TEST_APP_NAME
        )

    def test_change_store_name__too_long(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_language, app.play_store_language, '')
        # Now change it and check that the model reflects our change
        bad_play_store_name = 'N' * 31
        response = self._put(TEST_APP_ID,
                            {'app_store_name': TEST_APP_NAME,
                             'play_store_name': bad_play_store_name})
        self.assertEqual(response.status_code, 400)

        bad_app_store_name = 'N' * 266

        response = self._put(TEST_APP_ID,
                            {'app_store_name': bad_app_store_name,
                             'play_store_name': TEST_APP_NAME})
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            App.objects.get(app_id=TEST_APP_ID).app_store_name,
            App.objects.get(app_id=TEST_APP_ID).play_store_name,
            ''
        )

    def test_change_store_name__bumps_last_updated(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_name, app.play_store_name, '')
        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                        {'app_store_name': TEST_APP_NAME})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.app_store_name, TEST_APP_NAME)
        self.assertTrue(app.last_updated > current_last_updated)

        current_last_updated = app.last_updated
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                        {'play_store_name': TEST_APP_NAME})
        self.assertEqual(response.status_code, 200)
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.play_store_name, TEST_APP_NAME)
        self.assertTrue(app.last_updated > current_last_updated)

    def test_change_icons(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(len(app.icons.all()), 0)
        # Now change it and check that the model reflects our change
        response = self._put(TEST_APP_ID,
                  {'icons': json.dumps([TEST_APP_ICON_IOS])})
        self.assertEqual(response.status_code, 200)
        try:
            icon = app.icons.get(name=TEST_APP_ICON_IOS['name'])
            self.assertEqual(icon.platform, TEST_APP_ICON_IOS['platform']),
            self.assertEqual(icon.width, icon.height,
                             TEST_APP_ICON_IOS['height']),
            self.assertEqual(icon.image_format,
                             TEST_APP_ICON_IOS['image_format'])
        except ObjectDoesNotExist:
            self.fail('No icon found')

        # Check that the previous icon has been replaced by the new one
        response = self._put(TEST_APP_ID,
                        {'icons': json.dumps([TEST_APP_ICON_ANDROID])})
        self.assertEqual(response.status_code, 200)
        icons = list(app.icons.filter(name=TEST_APP_ICON_ANDROID['name']))
        self.assertEqual(len(icons), 1)
        icon = icons[0]
        self.assertEqual(icon.platform, TEST_APP_ICON_ANDROID['platform']),
        self.assertEqual(icon.width, icon.height,
                         TEST_APP_ICON_ANDROID['height']),
        self.assertEqual(icon.image_format,
                         TEST_APP_ICON_ANDROID['image_format'])

    def test_change_icons__set_no_icons(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        response = self._put(TEST_APP_ID,
                        {'icons': json.dumps([TEST_APP_ICON_IOS,
                                              TEST_APP_ICON_ANDROID])})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(app.icons.all()), 2)

        response = self._put(TEST_APP_ID, {'icons': json.dumps([])})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(app.icons.all()), 0)

    def test_change_icons__bad_dimensions(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(len(app.icons.all()), 0)

        bad_icon = deepcopy(TEST_APP_ICON_IOS)
        bad_icon['height'] = 5
        response = self._put(TEST_APP_ID, {'icons': json.dumps([bad_icon])})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(app.icons.all()), 0)

    def test_change_icons__bad_name(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(len(app.icons.all()), 0)

        bad_icon = deepcopy(TEST_APP_ICON_IOS)
        bad_icon['name'] = 'NOT_INDEX'
        response = self._put(TEST_APP_ID, {'icons': json.dumps([bad_icon])})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(app.icons.all()), 0)
