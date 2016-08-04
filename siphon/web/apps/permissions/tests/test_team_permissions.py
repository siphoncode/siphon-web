
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from siphon.web.apps.apps.models import App
from siphon.web.apps.subscriptions.models import Subscription
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.utils.test_utils import (
    with_new_app,
    with_new_subscribed_user,
    TEST_USER_USERNAME
)
from siphon.web.apps.permissions.tests import (
    to_json,
    PermissionsTestCase,
    OTHER_USER_EMAIL
)
from siphon.web.apps.permissions.tests.common import (
    TestPermissionsSharing,
    TestPermissionsInvitation
)


class TestTeamPermissionsSharing(TestPermissionsSharing, TestCase):
    def setUp(self):
        self.permission_type = AppPermission.TYPE_TEAM_MEMBER
        super(TestTeamPermissionsSharing, self).setUp()

    @with_new_app
    def test_team_sharing_only_for_paid_members(self):
        # Make sure user has no paid subscription.
        user = User.objects.get(username=TEST_USER_USERNAME)
        self.assertEqual(Subscription.objects.filter(user=user).count(), 0)

        self._login()
        obj, status = self._share(AppPermission.TYPE_TEAM_MEMBER,
            OTHER_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        msg = 'Sorry, you need a paid subscription to share an app with ' \
            'your team. Learn more here: https://getsiphon.com%s' % \
            reverse('static:pricing')
        self.assertTrue(msg in obj['detail'], obj)

    @with_new_app
    @with_new_subscribed_user
    def test_team_sharing_plan_allowance(self):
        user = User.objects.get(username=TEST_USER_USERNAME)
        plan = Subscription.objects.get(user=user).plan
        plan.team_sharing = False
        plan.save()

        self._login()
        obj, status = self._share(AppPermission.TYPE_TEAM_MEMBER,
            OTHER_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        msg = 'Sorry, your paid subscription plan does not include ' \
            'team sharing. Learn more and upgrade here: ' \
            'https://getsiphon.com%s' % reverse('static:pricing')
        self.assertTrue(msg in obj['detail'], obj)


class TestTeamPermissionsInvitation(TestPermissionsInvitation, TestCase):
    def setUp(self):
        self.permission_type = AppPermission.TYPE_TEAM_MEMBER
        super(TestTeamPermissionsInvitation, self).setUp()


class TestTeamPermissionsAliasing(PermissionsTestCase, TestCase):
    def setUp(self):
        self.permission_type = AppPermission.TYPE_TEAM_MEMBER
        super(TestTeamPermissionsAliasing, self).setUp()

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
        self.assertNotEqual(app.user.username, alias.user.username)
        self.assertNotEqual(app.app_id, alias.app_id)

    @with_new_app
    @with_new_subscribed_user
    def test_streamer_log_writer_fails(self):
        """
        This endpoint should return an error if called with the shared
        App ID:

        GET /streamers/?type=log_writer&app_id=<original-app-id>
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()

        resp = self.client.get(reverse('api:streamers:streamers'), {
            'type': 'log_writer',
            'app_id': app_permission.app.app_id
        })
        obj = to_json(resp)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('Sorry, you can not write logs to a shared team app.' \
            in obj.get('message', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_delete_of_original_app_id_fails(self):
        """
        DELETE /apps/<team-app-id> should fail with an error for the team
        member.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()
        obj, status = self._delete(app_permission.app.app_id)
        self.assertEqual(status, 404, obj)
        self.assertTrue('Not found.' in obj.get('detail', ''), obj)

        # Ensure that neither app was deleted.
        for app_id in (app_permission.app.app_id,
        app_permission.get_aliased_app().app_id):
            a = App.objects.get(app_id=app_id)
            self.assertEqual(a.deleted, False)

    @with_new_app
    @with_new_subscribed_user
    def test_PUT_of_original_app_id_fails(self):
        """
        PUT /apps/<team-app-id> should fail with an error for the team
        member.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()
        obj, status = self._put(app_permission.app.app_id)
        self.assertEqual(status, 404, obj)
        self.assertTrue('Not found.' in obj.get('detail', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_development_pull_of_original_app_id_fails(self):
        """
        Team member should not be able to do a development pull of the
        original App ID, only their internally aliased one. Example:

        /bundlers/?app_id=<app_id>&base_version=0.2&action=pull&platform=ios
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()

        # Do the development pull.
        obj, status = self._development_pull(app_permission.app.app_id)
        self.assertEqual(status, 400)
        self.assertTrue('Unknown app.' in obj.get('message', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_team_member_push_uses_aliased_app_id(self):
        """
        Check that when an accepted team member does a push it uses the
        user's internally aliased App ID, not the original.
        """
        # Share, accept and then grab the internal aliased App model.
        app_permission = self._share_and_accept()
        aliased_app = app_permission.get_aliased_app()

        self._login_as_other_user()
        app_id = app_permission.app.app_id
        obj, status = self._push(app_id)
        self.assertTrue(aliased_app.app_id in obj.get('bundler_url', ''), obj)
        self.assertTrue(app_id not in obj.get('bundler_url', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_team_member_push_with_deleted_permission(self):
        app_permission = self._share_and_accept()
        app_permission.deleted = True
        app_permission.save()

        obj, status = self._push(app_permission.app.app_id)
        self.assertTrue('Unknown app.' in obj.get('message', ''), obj)
        self.assertEqual(status, 400)

    @with_new_app
    @with_new_subscribed_user
    def test_team_member_push_with_inactive_permission(self):
        app_permission = self._share_and_accept()
        app_permission.active = False
        app_permission.save()

        obj, status = self._push(app_permission.app.app_id)
        self.assertTrue('Unknown app.' in obj.get('message', ''), obj)
        self.assertEqual(status, 400)

    @with_new_app
    @with_new_subscribed_user
    def test_team_member_apps_list_uses_internal_app_id(self):
        app_permission = self._share_and_accept()

        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps'))
        obj = to_json(resp)

        app_list = obj['results']
        self.assertEqual(len(app_list), 1)
        app_obj = app_list[0]
        self.assertEqual(
            app_obj['id'],
            app_permission.get_aliased_app().app_id
        )

    @with_new_app
    @with_new_subscribed_user
    def test_team_member_get_of_original_app_id_returns_alias(self):
        """
        GET /apps/<team-app-id> should return the team member's internally
        aliased app details, not the originally shared one.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()
        resp = self.client.get(reverse('api:apps:apps', kwargs={
            'app_id': app_permission.app.app_id
        }))
        obj = to_json(resp)
        self.assertTrue('id' in obj, obj)
        self.assertEqual(obj['id'], app_permission.get_aliased_app().app_id,
            obj)

    @with_new_app
    @with_new_subscribed_user
    def test_streamer_log_reader_uses_aliased_app_id(self):
        """
        This endpoint, when called with the shared App ID:

        GET /streamers/?app_id=<original-app-id>&type=log_reader

        Should return a "streamer_url" for the internally aliased App ID,
        not the original.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()

        obj, status = self._get_streamer_url(app_permission.app.app_id,
            'log_reader')
        self.assertEqual(status, 200, obj)
        streamer_url = obj['streamer_url']
        self.assertTrue(app_permission.get_aliased_app().app_id in \
            streamer_url)

    @with_new_app
    @with_new_subscribed_user
    def test_streamer_for_notifications_uses_aliased_app_id(self):
        """
        This endpoint, when called with the shared App ID:

        GET /streamers/?type=notifications&app_id=<original-app-id>

        Should return a "streamer_url" for the internally aliased App ID,
        not the original.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()

        obj, status = self._get_streamer_url(app_permission.app.app_id,
            'notifications')
        self.assertEqual(status, 200, obj)
        streamer_url = obj['streamer_url']
        self.assertTrue(app_permission.get_aliased_app().app_id in \
            streamer_url)

    @with_new_app
    @with_new_subscribed_user
    def test_publish_of_aliased_app_id_fails(self):
        """
        To avoid confusion, the team member should not be able to publish
        their internally aliased App ID. It should fail with an error.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()
        obj, status = self._publish(app_permission.get_aliased_app().app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('Sorry, a shared team app can only be published by ' \
            'the team leader.' in obj.get('detail', ''), obj)

    @with_new_app
    @with_new_subscribed_user
    def test_publish_of_original_app_id_fails(self):
        """
        Team member should not be able to do a publish of the original
        App ID that was shared with them.
        """
        app_permission = self._share_and_accept()
        self._login_as_other_user()

        obj, status = self._publish(app_permission.app.app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('Sorry, a shared team app can only be published by ' \
            'the team leader' in obj.get('detail', ''), obj)
