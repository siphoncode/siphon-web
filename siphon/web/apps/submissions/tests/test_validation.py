
import json

from django.test import client, TestCase
from django.core.urlresolvers import reverse

from siphon.web.apps.apps.models import App, AppIcon
from siphon.web.utils.test_utils import (
    with_new_app,
    TEST_USER_USERNAME,
    TEST_USER_PASSWORD,
    TEST_APP_ID,
)

class TestCheckSubmission(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    def _validate(self, app_id, platform='ios'):
        url = reverse('api:submissions:validate') + '?app_id=%s&platform=%s' % \
                     (app_id, platform)
        resp = self.client.get(url)
        return resp.status_code, json.loads(resp.content.decode('utf-8'))

    def test_validate__no_login(self):
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertEqual(status, 401)

    @with_new_app
    def test_validate__no_display_name(self):
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        app.display_name = ''
        app.save()
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertEqual(status, 400)
        # We expect an error message referencing the display of the app
        self.assertTrue('display_name' in obj['detail'])

    @with_new_app
    def test_validate__no_store_name(self):
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        app.app_store_name = ''
        app.play_store_name = ''
        app.save()
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertEqual(status, 400)
        # We expect an error message referencing the store name of the app
        self.assertTrue('store_name' in obj['detail'])
        status, obj = self._validate(TEST_APP_ID, 'android')
        self.assertEqual(status, 400)
        self.assertTrue('store_name' in obj['detail'])

    @with_new_app
    def test_validate__no_language(self):
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        app.app_store_language = ''
        app.play_store_language = ''
        app.save()
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertTrue('language' in obj['detail'])
        status, obj = self._validate(TEST_APP_ID, 'android')
        self.assertEqual(status, 400)
        self.assertTrue('language' in obj['detail'])

    @with_new_app
    def test_validate__no_icon(self):
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        AppIcon.objects.filter(app=app).delete()
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertTrue('icon' in obj['detail'])
        status, obj = self._validate(TEST_APP_ID, 'android')
        self.assertEqual(status, 400)
        self.assertTrue('icon' in obj['detail'])

    @with_new_app
    def test_validate_all_details(self):
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        app.save()

        icon = AppIcon(name='index', height=1024, width=1024, platform='ios',
                    image_format='png', app=app)
        icon.save()
        status, obj = self._validate(TEST_APP_ID, 'ios')
        self.assertEqual(status, 200)
