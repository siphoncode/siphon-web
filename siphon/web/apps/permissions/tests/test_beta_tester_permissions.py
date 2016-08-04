
from unittest.mock import patch

from django.core import mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from siphon.web.apps.apps.models import App
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.utils.test_utils import (
    with_new_app,
    with_new_subscribed_user,
    TEST_USER_USERNAME,
    TEST_APP_ID
)
from siphon.web.apps.permissions.tests import (
    PermissionsTestCase,
    to_json,
    OTHER_USER_USERNAME,
    OTHER_USER_EMAIL,
    SECOND_TESTER_USERNAME
)
from siphon.web.apps.permissions.tests.common import (
    TestPermissionsSharing,
    TestPermissionsInvitation
)

POST_NOTIFICATION_NAME = 'siphon.web.apps.apps.signals.handlers.' \
    'post_notification'


class TestBetaTesterPermissionsSharing(TestPermissionsSharing, TestCase):
    """ Common basic sharing tests. """
    def setUp(self):
        self.permission_type = AppPermission.TYPE_BETA_TESTER
        super(TestBetaTesterPermissionsSharing, self).setUp()

    @with_new_app
    def test_beta_testing_only_for_paid_members(self):
        # Make sure user has no paid subscription.
        user = User.objects.get(username=TEST_USER_USERNAME)
        self.assertEqual(Subscription.objects.filter(user=user).count(), 0)

        self._login()
        obj, status = self._share(AppPermission.TYPE_BETA_TESTER,
            OTHER_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        msg = 'Sorry, you need a paid subscription to share an app with ' \
            'beta testers. Learn more here: https://getsiphon.com%s' % \
            reverse('static:pricing')
        self.assertTrue(msg in obj['detail'], obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_testing_plan_allowance(self):
        user = User.objects.get(username=TEST_USER_USERNAME)
        plan = Subscription.objects.get(user=user).plan
        plan.beta_tester_sharing = False
        plan.save()

        self._login()
        obj, status = self._share(AppPermission.TYPE_BETA_TESTER,
            OTHER_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        msg = 'Sorry, your paid subscription plan does not include beta ' \
            'testing. Learn more and upgrade here: https://getsiphon.com%s' % \
            reverse('static:pricing')
        self.assertTrue(msg in obj['detail'], obj)

    @with_new_app
    @with_new_subscribed_user
    def test_get_sharing_status(self):
        self._share_with_both_testers()
        self._login()
        obj, status = self._get_sharing_status()
        self.assertEqual(status, 200, obj)
        usernames = [user_obj['username'] for user_obj in obj['shared_with']]
        self.assertEqual(len(usernames), 2)
        self.assertTrue(OTHER_USER_USERNAME in usernames)
        self.assertTrue(SECOND_TESTER_USERNAME in usernames)

        # The aliased app should be returned.
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(
            obj['aliased_app']['id'],
            app.beta_testing_alias.app_id
        )

    @with_new_app
    @with_new_subscribed_user
    def test_get_sharing_status__no_testers(self):
        self._login()
        obj, status = self._get_sharing_status()
        self.assertEqual(status, 200, obj)
        self.assertEqual(obj['shared_with'], [])

    @with_new_app
    @with_new_subscribed_user
    def test_get_sharing_status__creates_beta_tester_alias(self):
        app = App.objects.get(app_id=TEST_APP_ID)
        self.assertEqual(app.beta_testing_alias, None)
        del app

        self._login()
        obj, status = self._get_sharing_status()
        self.assertEqual(status, 200, obj)

        # The aliased app should be returned.
        self.assertEqual(
            obj['aliased_app']['id'],
            App.objects.get(app_id=TEST_APP_ID).beta_testing_alias.app_id
        )

    @with_new_app
    @with_new_subscribed_user
    def test_get_sharing_status__fails_for_team_member_type(self):
        self._login()
        obj, status = self._get_sharing_status(
            permission=AppPermission.TYPE_TEAM_MEMBER)
        self.assertEqual(status, 400)

    @with_new_app
    @with_new_subscribed_user
    def test_PUT_sends_notifications_to_all_testers(self):
        self._share_with_both_testers()
        alias = App.objects.get(app_id=TEST_APP_ID).get_beta_testing_alias()

        # Notification should have been sent to both testers.
        with patch(POST_NOTIFICATION_NAME) as fn:
            # Trigger updates.
            self._login()
            obj, status = self._put(alias.app_id)
            self.assertEqual(status, 200)

            self.assertEqual(len(fn.call_args_list), 3)
            usernames = []
            for kall in fn.call_args_list:
                payload = kall[0][0]
                # Should all be for same app.
                self.assertEqual(payload['app_id'], alias.app_id)
                self.assertEqual(payload['type'], 'app_updated')
                usernames.append(payload['user_id'])

            # App owner and both beta testers should have been notified.
            expected_usernames = [u.username for u in self._get_all_users()]
            self.assertEqual(sorted(expected_usernames), sorted(usernames),
                fn.call_args_list)

        # It should have sent notification emails to all of them too.
        messages = [m for m in mail.outbox if \
            'There is an update available' in m.subject]
        self.assertEqual(len(messages), 2)
        recipients = sorted([message.to[0] for message in messages])
        expected_emails = sorted([u.email for u in \
            AppPermission.get_beta_testers(alias.master_app)])
        self.assertEqual(recipients, expected_emails, recipients)

        app = App.objects.get(app_id=TEST_APP_ID)
        name = app.name
        if app.display_name:
            name = app.display_name
        for message in messages:
            self.assertTrue(name in message.subject)

    @with_new_app
    @with_new_subscribed_user
    def test_PUT_not_sends_notifications_to_all_testers__inactive(self):
        # Share and disable permission.
        app_permission = self._share_and_accept()
        alias_app = app_permission.app.get_beta_testing_alias()
        app_permission.active = False
        app_permission.save()

        with patch(POST_NOTIFICATION_NAME) as fn:
            # Trigger updates.
            self._login()
            obj, status = self._put(alias_app.app_id)
            self.assertEqual(status, 200)

            self.assertEqual(len(fn.call_args_list), 1)
            payload = fn.call_args[0][0]
            self.assertEqual(payload['user_id'], TEST_USER_USERNAME)

        # No notification emails should be sent.
        messages = [m for m in mail.outbox if \
            'There is an update available' in m.subject]
        self.assertEqual(len(messages), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_PUT_not_sends_notifications_to_all_testers__deleted(self):
        # Share and disable permission.
        app_permission = self._share_and_accept()
        alias_app = app_permission.app.get_beta_testing_alias()
        app_permission.deleted = True
        app_permission.save()

        with patch(POST_NOTIFICATION_NAME) as fn:
            # Trigger updates.
            self._login()
            obj, status = self._put(alias_app.app_id)
            self.assertEqual(status, 200)

            self.assertEqual(len(fn.call_args_list), 1)
            payload = fn.call_args[0][0]
            self.assertEqual(payload['user_id'], TEST_USER_USERNAME)

        # No notification emails should be sent.
        messages = [m for m in mail.outbox if \
            'There is an update available' in m.subject]
        self.assertEqual(len(messages), 0)


class TestBetaTesterPermissionsInvitation(TestPermissionsInvitation, TestCase):
    """ Common invitation tests. """
    def setUp(self):
        self.permission_type = AppPermission.TYPE_BETA_TESTER
        super(TestBetaTesterPermissionsInvitation, self).setUp()


class TestBetaTesterPermissionsAliasing(PermissionsTestCase, TestCase):
    def setUp(self):
        self.permission_type = AppPermission.TYPE_BETA_TESTER
        super(TestBetaTesterPermissionsAliasing, self).setUp()

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_copies_characteristics(self):
        """
        The aliased app should have the same name, display name etc. as the
        original app at the time of copying.
        """
        # Share and accept.
        app_permission = self._share_and_accept()
        self.assertTrue(app_permission.active, True)
        self.assertNotEqual(app_permission.get_aliased_app(), None)
        app = app_permission.app
        alias = app_permission.get_aliased_app()

        # These should be copied.
        self.assertEqual(app.name, alias.name)
        self.assertEqual(app.display_name, alias.display_name)
        self.assertEqual(app.facebook_app_id, alias.facebook_app_id)
        self.assertEqual(app.base_version.name, alias.base_version.name)

        # Sanity check.
        self.assertEqual(app.user.username, alias.user.username)
        self.assertNotEqual(app.app_id, alias.app_id)


class TestBetaTesterPermissionsOwnerAliasing(PermissionsTestCase, TestCase):
    """ Aliasing tests for the owner of the shared app. """
    def setUp(self):
        self.permission_type = AppPermission.TYPE_BETA_TESTER
        super(TestBetaTesterPermissionsOwnerAliasing, self).setUp()

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_is_owned_by_original_app_owner(self):
        """
        The read-only aliased app that is created for beta tests should be
        owned by the original app owner who did the sharing.
        """
        app_permission = self._share_and_accept()
        self.assertEqual(app_permission.get_aliased_app().user.username,
            TEST_USER_USERNAME)

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_is_not_created_for_each_beta_tester(self):
        """
        `AppPermission.aliased_app` field itself should always be None.
        """
        perm1, perm2 = self._share_with_both_testers()
        self.assertEqual(perm1.aliased_app, None)
        self.assertEqual(perm2.aliased_app, None)

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_is_the_same_for_each_beta_tester(self):
        perm1, perm2 = self._share_with_both_testers()
        self.assertNotEqual(perm1.get_aliased_app(), None)
        self.assertEqual(perm1.get_aliased_app(), perm2.get_aliased_app())

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_does_not_appear_in_owners_app_list(self):
        """
        The original app owner who did the sharing should not see the aliased
        app in their list of apps, even though they own it.
        """
        app_permission = self._share_and_accept()
        self.assertTrue(app_permission.get_aliased_app() is not None)
        self._login()  # log back in as owner.
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)
        self.assertEqual(len(obj['results']), 1)
        app_ids = [app_obj['id'] for app_obj in obj['results']]
        self.assertTrue(app_permission.app.app_id in app_ids)
        self.assertTrue(app_permission.get_aliased_app().app_id not in app_ids)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_still_push_to_original_app(self):
        app_permission = self._share_and_accept()
        self._login()  # log back in as owner.
        original_app_id = app_permission.app.app_id
        obj, status = self._push(original_app_id)
        self.assertEqual(status, 200, obj)
        self.assertTrue(original_app_id in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_push_to_aliased_app(self):
        app_permission = self._share_and_accept()
        self._login()  # log back in as owner.
        aliased_app_id = app_permission.get_aliased_app().app_id
        obj, status = self._push(aliased_app_id)
        self.assertEqual(status, 200, obj)
        self.assertTrue(aliased_app_id in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_push_to_aliased_app__pre_acceptance(self):
        app_permission = self._share_and_dont_accept()
        self._login()  # log back in as owner.
        aliased_app_id = app_permission.get_aliased_app().app_id
        obj, status = self._push(aliased_app_id)
        self.assertEqual(status, 200, obj)
        self.assertTrue(aliased_app_id in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_push_to_aliased_app__permission_deleted(self):
        app_permission = self._share_and_accept()
        app_permission.deleted = True
        app_permission.save()

        self._login()  # log back in as owner.
        aliased_app_id = app_permission.get_aliased_app().app_id
        obj, status = self._push(aliased_app_id)
        self.assertEqual(status, 200, obj)
        self.assertTrue(aliased_app_id in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_push_to_aliased_app__permission_inactive(self):
        app_permission = self._share_and_accept()
        app_permission.active = False
        app_permission.save()

        self._login()  # log back in as owner.
        aliased_app_id = app_permission.get_aliased_app().app_id
        obj, status = self._push(aliased_app_id)
        self.assertEqual(status, 200, obj)
        self.assertTrue(aliased_app_id in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_get_individual_aliased_app(self):
        app_permission = self._share_and_accept()
        self._login()  # log back in as owner.
        resp = self.client.get(reverse('api:apps:apps', kwargs={
            'app_id': app_permission.get_aliased_app().app_id
        }))
        obj = to_json(resp)
        self.assertEqual(resp.status_code, 200, obj)
        self.assertEqual(obj['id'], app_permission.get_aliased_app().app_id)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_development_pull_aliased_app(self):
        app_permission = self._share_and_accept()
        self._login()  # log back in as owner.
        obj, status = self._development_pull(
            app_permission.get_aliased_app().app_id)
        self.assertEqual(status, 400)
        self.assertTrue('App owner can not pull a beta testing app' in \
            obj.get('message', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_delete_aliased_app(self):
        app_permission = self._share_and_accept()
        self._login()  # log back in as owner.
        obj, status = self._delete(app_permission.get_aliased_app().app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('App owner can not delete a beta testing app' in \
            obj.get('detail', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_write_streamer_logs_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id

        self._login()  # owner.
        obj, status = self._get_streamer_url(alias_app_id, 'log_writer')
        self.assertEqual(status, 400, obj)
        self.assertTrue('streamer_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_read_streamer_logs_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id

        self._login()  # owner.
        obj, status = self._get_streamer_url(alias_app_id, 'log_reader')
        self.assertEqual(status, 200, obj)
        self.assertTrue('streamer_url' in obj)
        self.assertTrue(alias_app_id in obj['streamer_url'])

    @with_new_app
    @with_new_subscribed_user
    def test_owner_can_not_read_streamer_notifications_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id

        self._login()  # owner.
        obj, status = self._get_streamer_url(alias_app_id, 'notifications')
        self.assertEqual(status, 400, obj)
        self.assertTrue('streamer_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_owner_publish_of_aliased_app_id_fails(self):
        """
        The app owner of an app shared with beta testers should not be able
        to publish the aliased app. It should fail with an error.
        """
        app_permission = self._share_and_accept()
        self._login()
        resp = self.client.post(reverse('api:submissions:submissions'), {
            'app_id': app_permission.get_aliased_app().app_id,
            'platform': 'ios',
            'platform_username': 'dummy',
            'platform_password': 'dummy'
        })
        obj = to_json(resp)
        self.assertEqual(resp.status_code, 400, obj)
        self.assertTrue('This app can not be published.' in \
            obj.get('detail', ''), obj)


class TestBetaTesterPermissionsTesterAliasing(PermissionsTestCase, TestCase):
    """ Aliasing tests for the beta tester. """
    def setUp(self):
        self.permission_type = AppPermission.TYPE_BETA_TESTER
        super(TestBetaTesterPermissionsTesterAliasing, self).setUp()

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_appears_in_testers_apps_list(self):
        """
        The beta tester should see the aliased app in their /apps list,
        so that it appears in the sandbox.
        """
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)
        self.assertEqual(len(obj['results']), 1)
        self.assertEqual(obj['results'][0]['id'], alias_app_id)

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_does_not_appear_in_apps_list__inactive(self):
        """
        The beta tester must accept the invitation before the aliased app
        appears in their list.
        """
        app_permission = self._share_and_accept()
        app_permission.active = False
        app_permission.save()
        del app_permission

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)
        self.assertEqual(len(obj['results']), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_does_not_appear_in_apps_list__deleted(self):
        """
        Aliased app shouldn't appear in beta testers list if the AppPermission
        model has been marked as deleted.
        """
        app_permission = self._share_and_accept()
        app_permission.deleted = True
        app_permission.save()
        del app_permission

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)
        self.assertEqual(len(obj['results']), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_aliased_app_does_not_appear_in_apps_list__original_deleted(self):
        """
        Aliased app shouldn't appear in beta testers list if original
        shared app was deleted by the owner.
        """
        app_permission = self._share_and_accept()
        app_permission.app.deleted = True
        app_permission.app.save()
        del app_permission

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)
        self.assertEqual(len(obj['results']), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_dev_pull_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._development_pull(alias_app_id)
        self.assertEqual(status, 200, obj)
        bundler_url = obj['bundler_url']
        self.assertTrue(alias_app_id in bundler_url)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_dev_pull_aliased_app__deleted(self):
        app_permission = self._share_and_accept()
        app_permission.deleted = True
        app_permission.save()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._development_pull(alias_app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('bundler_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_dev_pull_aliased_app__inactive(self):
        app_permission = self._share_and_accept()
        app_permission.active = False
        app_permission.save()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._development_pull(alias_app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('bundler_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_dev_pull_aliased_app__original_deleted(self):
        """
        If the original shared app is deleted, beta tester should not be able
        to do a development pull of the aliased app.
        """
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        app_permission.app.deleted = True
        app_permission.app.save()
        del app_permission

        self._login_as_other_user()
        obj, status = self._development_pull(alias_app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('bundler_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_delete_of_aliased_app_deletes_share_permission(self):
        """
        If the beta tester does a DELETE of the aliased app (i.e. through
        the dashboard) then it should set deleted=True on the AppPermission
        model, thus removing the shared app from the user's account.
        """
        app_permission = self._share_and_accept()
        invite_code = app_permission.invite_code
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._delete(alias_app_id)
        self.assertEqual(status, 200)

        # App and alias app should not be deleted.
        self.assertEqual(App.objects.get(app_id=TEST_APP_ID).deleted, False)
        self.assertEqual(App.objects.get(app_id=alias_app_id).deleted, False)

        # Only the permission should be deleted.
        app_permission = AppPermission.objects.get(invite_code=invite_code)
        self.assertEqual(app_permission.deleted, True)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_PUT_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._put(alias_app_id)
        self.assertEqual(status, 404)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_push_to_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._push(alias_app_id)
        self.assertEqual(status, 400)
        self.assertTrue('bundler_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_publish_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._publish(alias_app_id)
        self.assertEqual(status, 400)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_write_streamer_logs_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._get_streamer_url(alias_app_id, 'log_writer')
        self.assertEqual(status, 200, obj)
        self.assertTrue('streamer_url' in obj)
        self.assertTrue(alias_app_id in obj['streamer_url'])

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_not_read_streamer_logs_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._get_streamer_url(alias_app_id, 'log_reader')
        self.assertEqual(status, 400, obj)
        self.assertTrue('streamer_url' not in obj)

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_read_streamer_notifications_for_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        obj, status = self._get_streamer_url(alias_app_id, 'notifications')
        self.assertEqual(status, 200, obj)
        self.assertTrue('streamer_url' in obj)
        self.assertTrue(alias_app_id in obj['streamer_url'])

    @with_new_app
    @with_new_subscribed_user
    def test_beta_tester_can_get_individual_aliased_app(self):
        app_permission = self._share_and_accept()
        alias_app_id = app_permission.get_aliased_app().app_id
        del app_permission

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps', kwargs={
            'app_id': alias_app_id
        }))
        obj = to_json(resp)
        self.assertEqual(resp.status_code, 200, obj)
        self.assertEqual(obj['id'], alias_app_id)
