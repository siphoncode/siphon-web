
import json
from decimal import Decimal

from django.test import client, TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.submissions.models import Submission
from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.test_utils import (
    with_new_app,
    with_new_subscribed_user,
    with_submission,
    TEST_USER_USERNAME,
    TEST_USER_PASSWORD,
    TEST_APP_ID,
    TEST_APP_BASE_VERSION
)

class TestCheckSubmission(TestCase):
    def setUp(self):
        self.client = client.Client()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    def _check(self, app_id, platform='ios'):
        url = reverse('api:submissions:check') + '?app_id=%s&platform=%s' % \
                     (app_id, platform)
        resp = self.client.get(url)
        return resp.status_code, json.loads(resp.content.decode('utf-8'))

    @with_new_app
    def test_check__no_previous_submissions(self):
        self._login()
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], True)

    @with_submission
    def test_check__hard_update__base_version(self):
        self._login()
        # By default the app has the same base_version/display_name as the test
        # submission model, so its a soft update
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], False)
        # Bump the app up to a newer base_version
        app = App.objects.get(app_id=TEST_APP_ID)
        app.base_version = BaseVersion.objects.create(
            name=str(Decimal(app.base_version.name) + 1),
            latest=True,
            react_native_version='0.22.2'
        )
        app.save()
        # Should be a hard update
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], True)

    @with_submission
    def test_check__hard_update__display_name(self):
        self._login()
        # By default the app has the same base_version/display_name as the test
        # submission model, so its a soft update
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], False)
        # Change the app's display_name
        app = App.objects.get(app_id=TEST_APP_ID)
        app.display_name = 'A new one'
        app.save()
        # Should be a hard update
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], True)

    @with_submission
    def test_check__soft_update(self):
        self._login()
        # By default the app has the same base_version/display_name as the test
        # submission model, so its a soft update
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(obj['hard_update_required'], False)

    @with_submission
    def test_check__another_users_app(self):
        """ Shouldn't work for another user's app. """
        # Log in as another user
        other_user = User.objects.create_user(
            'other_user', 'other@other.com')
        other_user.set_password('blablabla')
        other_user.save()
        self.client.login(username='other_user', password='blablabla')
        # The check should not work
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 400)
        self.assertTrue('hard_update_required' not in obj)

    @with_submission
    def test_check__not_authorized(self):
        """ Shouldn't work if not logged in at all. """
        status, obj = self._check(TEST_APP_ID)
        self.assertEqual(status, 401)
        self.assertTrue('hard_update_required' not in obj)


class TestSubmissions(TestCase):
    def setUp(self):
        self.client = client.Client()
        self.other_user = User.objects.create_user(
            'other_user', 'other@other.com')
        self.other_user.set_password('blablabla')
        self.other_user.save()

    def _login(self):
        self.client.login(
            username=TEST_USER_USERNAME,
            password=TEST_USER_PASSWORD
        )

    def _login_other_user(self):
        self.client.login(
            username=self.other_user.username,
            password='blablabla'
        )

    def _submit(self, app_id, platform='ios', platform_username='a@b.com',
                platform_password='abc111'):
        payload = {
            'app_id': app_id,
            'platform_username': platform_username,
            'platform_password': platform_password
        }

        if platform:
            payload['platform'] = platform
        resp = self.client.post(reverse('api:submissions:submissions'), payload)
        return resp.status_code, json.loads(resp.content.decode('utf-8'))

    @with_new_subscribed_user
    @with_new_app
    def test_submission__valid(self):
        # Do the submission
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertTrue('id' in obj and isinstance(obj['id'], str))
        self.assertEqual(obj['app_id'], TEST_APP_ID)
        self.assertEqual(obj['status'], 'processing')
        self.assertEqual(Submission.objects.all().count(), 1)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__no_display_name_set(self):
        self.assertEqual(Submission.objects.all().count(), 0)
        # Make sure that App.display_name is not set
        app = App.objects.get(app_id=TEST_APP_ID)
        app.display_name = ''
        app.save()
        # Try to submit, it should fail
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 400)
        self.assertEqual(Submission.objects.all().count(), 0)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__bad_platform_name(self):
        self._login()
        # Missing platform
        status, obj = self._submit(TEST_APP_ID, platform='')
        self.assertEqual(status, 400)
        # Bad platform (platform other than ios or android shouldn't work)
        status, obj = self._submit(TEST_APP_ID, platform='windows')
        self.assertEqual(status, 400)

    @with_new_subscribed_user
    @with_new_app
    def _test_submission__hard_update_requires_platform_info(self, platform):
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Activate the submission so that we can submit again
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = True
        previous.is_failed = False
        previous.save()
        # Change the app's display_name so that we have to do a hard update
        app = App.objects.get(app_id=TEST_APP_ID)
        app.display_name = 'A brand new display name'
        app.save()
        self.assertEqual(Submission.app_requires_hard_update(app, platform), True)
        # Missing platform_username
        status, obj = self._submit(TEST_APP_ID, platform=platform,
                                   platform_username='')
        self.assertEqual(status, 400)
        # Missing platform_password
        status, obj = self._submit(TEST_APP_ID, platform=platform,
                                   platform_password='')
        self.assertEqual(status, 400)

    def test_submission__hard_update_requires_platform_info_ios(self):
        self._test_submission__hard_update_requires_platform_info('ios')

    def test_submission__hard_update_requires_platform_info_android(self):
        self._test_submission__hard_update_requires_platform_info('android')

    # @with_new_subscribed_user
    # @with_new_app
    # def _test_submission__soft_update_requires_no_platform_info(self, platform):
    #     # Do a valid submission
    #     self._login()
    #     status, obj = self._submit(TEST_APP_ID, platform=platform)
    #     self.assertEqual(Submission.objects.all().count(), 1)
    #     # Activate the submission so that we can submit again
    #     previous = Submission.objects.get(submission_id=obj['id'])
    #     previous.is_active = True
    #     previous.is_failed = False
    #     previous.save()
    #     # At this point we should be able to do a soft update
    #     app = App.objects.get(app_id=TEST_APP_ID)
    #     self.assertEqual(Submission.app_requires_hard_update(app, platform),
    #                     False)
    #     # Now we should be able to submit with no platform info
    #     status, obj = self._submit(TEST_APP_ID, platform_username='',
    #         platform_password='', platform=None)
    #     self.assertEqual(status, 200)
    #     self.assertTrue('id' in obj and isinstance(obj['id'], str))
    #
    # def test_submission__soft_update_requires_no_platform_info_ios(self):
    #     self._test_submission__soft_update_requires_no_platform_info('ios')
    #
    # def test_submission__soft_update_requires_no_platform_info_android(self):
    #     self._test_submission__soft_update_requires_no_platform_info('android')

    @with_new_subscribed_user
    @with_new_app
    def test_submission__not_authorized(self):
        """ Trying to submit a real app without logging in should fail. """
        # Try to submit without logging in at all.
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 401)
        self.assertEqual(obj['detail'], 'Not authorized.')
        self.assertEqual(Submission.objects.all().count(), 0)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__bad_app_id(self):
        """ Trying to submit another user's app should fail. """
        self._login_other_user()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 400)
        self.assertTrue('detail' in obj)
        self.assertEqual(Submission.objects.all().count(), 0)

    @with_new_app
    def test_submission__no_subscription(self):
        # i.e. user literally has no Subscription model.
        user = User.objects.get(username=TEST_USER_USERNAME)
        self.assertEqual(Subscription.objects.filter(user=user).count(), 0)
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 400)
        self.assertTrue('detail' in obj)
        self.assertEqual(Submission.objects.all().count(), 0)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__bad_subscription(self):
        """ Should not be able to submit with an inactive subscription. """
        # Deactivate the subscription.
        user = User.objects.get(username=TEST_USER_USERNAME)
        sub = Subscription.objects.get(user=user)
        sub.active = False
        sub.save()
        # Submit should fail
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 400)
        self.assertTrue('detail' in obj)
        self.assertEqual(Submission.objects.all().count(), 0)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__already_submitted_a_different_app(self):
        """
        Publishing should fail if this user has already submitted a different
        app, i.e. for now they can only publish one app on both ' \
        'platforms. We'll need to support multiple apps-per-user at some '
        'point in the future though!
        """
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform='ios')
        self.assertEqual(Submission.objects.all().count(), 1)
        # Try to submit a different app again for the same platform
        new_app_id = 'a-new-app'
        App.objects.create(
            user=User.objects.get(username=TEST_USER_USERNAME),
            app_id=new_app_id,
            name='a-new-app',
            display_name='A New App',
            base_version=BaseVersion.objects.get(name=TEST_APP_BASE_VERSION)
        )
        status, obj = self._submit(new_app_id, platform='ios')
        self.assertEqual(status, 400)
        self.assertTrue('detail' in obj)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Try to submit a different app for a different platform (should fail)
        status, obj = self._submit(new_app_id, platform='android')
        self.assertEqual(status, 400)
        self.assertTrue('detail' in obj)
        self.assertEqual(Submission.objects.all().count(), 1)

    @with_new_subscribed_user
    @with_new_app
    def test_submission__same_app_different_platform(self):
        # Try to submit the same app for a different platform (should succeed)
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform='ios')
        self.assertEqual(Submission.objects.all().count(), 1)
        status, obj = self._submit(TEST_APP_ID, platform='android')
        self.assertEqual(status, 200)
        self.assertEqual(Submission.objects.all().count(), 2)

    @with_new_subscribed_user
    @with_new_app
    def _test_submission__previous_submission__inactive(self, platform):
        """
        This covers the case where a previous submission is still in the
        build queue or still awaiting approval.
        """
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Make sure its inactive
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = False
        previous.is_failed = False
        previous.save()
        # Do another subission, it should fail.
        status, obj = self._submit(TEST_APP_ID, platform)
        self.assertEqual(status, 400)
        self.assertTrue('already in the publishing queue' in obj['detail'])
        self.assertEqual(Submission.objects.all().count(), 1)

    def test_submission__previous_submission__inactive_ios(self):
        self._test_submission__previous_submission__inactive('ios')

    def test_submission__previous_submission__inactive_android(self):
        self._test_submission__previous_submission__inactive('android')

    @with_new_subscribed_user
    @with_new_app
    def _test_submission__previous_submission__failed(self, platform):
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Make sure its inactive *and* the submission failed
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = False
        previous.is_failed = True
        previous.save()
        # Do another subission, it should let them do it.
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(status, 200)
        self.assertEqual(Submission.objects.all().count(), 2)

    def test_submission__previous_submission__failed_ios(self):
        self._test_submission__previous_submission__failed('ios')

    def test_submission__previous_submission__failed_android(self):
        self._test_submission__previous_submission__failed('android')

    @with_new_subscribed_user
    @with_new_app
    def _test_submission__previous_submission__active(self, platform):
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Make sure its active and didn't fail
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = True
        previous.is_failed = False
        previous.save()
        # Do another submission, it should let them do it.
        status, obj = self._submit(TEST_APP_ID, platform)
        self.assertEqual(status, 200)
        self.assertEqual(Submission.objects.all().count(), 2)

    def test_submission__previous_submission__active_ios(self):
        self._test_submission__previous_submission__active('ios')

    def test_submission__previous_submission__active_android(self):
        self._test_submission__previous_submission__active('android')

    @with_new_subscribed_user
    @with_new_app
    def test_submission__hard_update_required(self):
        # If another app is submitted for a different platform, then
        # this too requires a hard update.
        self._login()
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'ios'), True)
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'android'), True)
        status, obj = self._submit(TEST_APP_ID, platform='ios')
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'ios'), False)
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'android'), True)
        status, obj = self._submit(TEST_APP_ID, platform='android')
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'ios'), False)
        self.assertEqual(Submission.app_requires_hard_update(app,
                        'android'), False)

    @with_new_subscribed_user
    @with_new_app
    def test_delete_app_with_submission(self):
        """
        Should not be able to delete an app that has one-or-more submissions.
        """
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Make sure the app exists and is not yet deleted
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)
        # Try to delete the app
        url = reverse('api:apps:apps', kwargs={'app_id': TEST_APP_ID})
        response = self.client.delete(url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).deleted is False)

    @with_new_subscribed_user
    @with_new_app
    def _test_soft_update(self, platform):
        """
        Soft updates should skip the processing step and get released
        right away.
        """
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Activate the submission so that we can submit again
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = True
        previous.is_failed = False
        previous.save()
        # At this point we should be able to do a soft update
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(Submission.app_requires_hard_update(app, platform),
                         False)
        # Do a soft update (i.e. no app metadata has changed), it should be
        # released straight away
        status, obj = self._submit(TEST_APP_ID, platform=platform)
        self.assertEqual(status, 200)
        self.assertEqual(Submission.objects.all().count(), 2)
        latest = Submission.objects.get(submission_id=obj['id'])
        self.assertEqual(latest.is_active, True)
        self.assertEqual(latest.is_failed, False)
        self.assertEqual(latest.status, Submission.STATUS_RELEASED)

    def test_soft_update_ios(self):
        self._test_soft_update('ios')

    def test_soft_update_android(self):
        self._test_soft_update('android')

    @with_new_subscribed_user
    @with_new_app
    def _test_hard_update(self, platform):
        """
        Hard updates should get marked as processing and not be active
        straight away after a submit.
        """
        # Do a valid submission
        self._login()
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(Submission.objects.all().count(), 1)
        # Activate the submission so that we can submit again
        previous = Submission.objects.get(submission_id=obj['id'])
        previous.is_active = True
        previous.is_failed = False
        previous.save()
        # Change the app's display_name so that we have to do a hard update
        app = App.objects.get(app_id=TEST_APP_ID)
        app.display_name = 'A brand new display name'
        app.save()
        self.assertEqual(Submission.app_requires_hard_update(app, platform),
                         True)
        # Do a hard update, it should not be active yet.
        status, obj = self._submit(TEST_APP_ID)
        self.assertEqual(status, 200)
        self.assertEqual(Submission.objects.all().count(), 2)
        latest = Submission.objects.get(submission_id=obj['id'])
        self.assertEqual(latest.is_active, False)
        self.assertEqual(latest.is_failed, False)
        self.assertEqual(latest.status, Submission.STATUS_PROCESSING)

    def test_hard_update_ios(self):
        self._test_hard_update('ios')

    def test_hard_update_android(self):
        self._test_hard_update('android')

    @with_new_subscribed_user
    @with_new_app
    def test_submission_with_pre_release_base_version_fails(self):
        # Bump the app up to a pre-release base_version
        app = App.objects.get(app_id=TEST_APP_ID)
        app.base_version = BaseVersion.objects.create(
            name=str(Decimal(app.base_version.name) + 1),
            latest=False,
            react_native_version='0.22.2'
        )
        app.save()
        # Submission should fail.
        self._login()
        status, obj = self._submit(TEST_APP_ID, platform='ios')
        self.assertEqual(status, 400, obj)
        self.assertTrue('is not yet released' in obj.get('detail', ''), obj)
        self.assertEqual(Submission.objects.all().count(), 0)
