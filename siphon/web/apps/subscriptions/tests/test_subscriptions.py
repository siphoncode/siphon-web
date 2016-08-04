
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse

from siphon.web.apps.apps.models import App
from siphon.web.apps.streamers.models import Streamer
from siphon.web.utils.test_utils import with_new_user, TEST_USER_USERNAME


class TestWebhook(TestCase):
    def setUp(self):
        self.client = client.Client()

    @with_new_user
    def test_webhook_security(self):
        data = {
            'content': {},
            'id': 'bad-id',
            'event_type': 'subscription_created'
        }
        url = reverse('api:subscriptions:chargebee_webhook')
        response = self.client.post(url, data=json.dumps(data),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
