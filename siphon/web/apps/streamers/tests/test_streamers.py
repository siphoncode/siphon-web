
import json
from decimal import Decimal

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.apps.models import App
from siphon.web.apps.streamers.models import Streamer
from siphon.web.utils.test_utils import (
    with_new_app,
    TEST_APP_NAME,
    TEST_APP_ID,
    TEST_APP_BASE_VERSION,
    TEST_USER_USERNAME,
    TEST_USER_PASSWORD,
    TEST_USER_EMAIL
)


def _to_dict(response):
    return json.loads(response.content.decode('utf-8'))

def _get_streamer_url(client, stream_type, app_id):
    response = client.get(reverse('api:streamers:streamers'), {
        'type': stream_type,
        'app_id': app_id
    })
    return _to_dict(response)


class TestStreamerTypes(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    @with_new_app
    def test_notifications_type(self):
        # Filtered for a specific app_id
        self._login()
        stream_type = 'notifications'
        obj = _get_streamer_url(self.client, stream_type, app_id=TEST_APP_ID)
        url = obj.get('streamer_url')
        self.assertNotEqual(url, None)
        self.assertTrue(TEST_APP_ID in url and stream_type in url)

    @with_new_app
    def test_notifications_type__wildcard(self):
        # Special wildcard endpoint for Siphon Sandbox
        self._login()
        stream_type = 'notifications'
        obj = _get_streamer_url(self.client, stream_type, app_id='*')
        url = obj.get('streamer_url')
        self.assertNotEqual(url, None)
        self.assertTrue(TEST_APP_ID not in url and stream_type in url)
        self.assertTrue('app_id=*' in url)

    @with_new_app
    def test_log_reader_type(self):
        self._login()
        stream_type = 'log_reader'
        obj = _get_streamer_url(self.client, stream_type, app_id=TEST_APP_ID)
        url = obj.get('streamer_url')
        self.assertNotEqual(url, None)
        self.assertTrue(TEST_APP_ID in url and stream_type in url)

    @with_new_app
    def test_log_writer_type(self):
        self._login()
        stream_type = 'log_writer'
        obj = _get_streamer_url(self.client, stream_type, app_id=TEST_APP_ID)
        url = obj.get('streamer_url')
        self.assertNotEqual(url, None)
        self.assertTrue(TEST_APP_ID in url and stream_type in url)


class TestStreamerSecurity(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    @with_new_app
    def test_authentication(self):
        """ Should not be able to get streamer URL for another user's app. """
        other_user = User.objects.create_user(
            username='other_user',
            email='other@user.com'
        )
        other_user.set_password('bananas')
        other_user.save()
        self.client.login(username='other_user', password='bananas')
        for stream_type in Streamer.STREAM_TYPES:
            obj = _get_streamer_url(self.client, stream_type,
                app_id=TEST_APP_ID)
            self.assertEqual(obj['message'], 'Unknown app.')

    @with_new_app
    def test_wss(self):
        """
        For each stream type, we should always be given an wss:// secure URL
        for the streamer server.
        """
        self._login()
        for stream_type in Streamer.STREAM_TYPES:
            obj = _get_streamer_url(self.client, stream_type,
                app_id=TEST_APP_ID)
            self.assertTrue('streamer_url' in obj)
            self.assertTrue(obj['streamer_url'].startswith('wss://'))
