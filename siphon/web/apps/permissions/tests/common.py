
from django.contrib.auth.models import User
from django.core import mail

from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.apps.permissions.tests import (
    PermissionsTestCase,
    OTHER_USER_USERNAME,
    OTHER_USER_EMAIL
)
from siphon.web.utils.test_utils import (
    with_new_app,
    with_new_subscribed_user,
    TEST_USER_USERNAME,
    TEST_USER_EMAIL,
    TEST_APP_ID,
    TEST_APP_BASE_VERSION
)


class TestPermissionsSharing(PermissionsTestCase):
    """
    Note: this is abstract, subclasses must also inherit TestCase and define
    their own setUp() with `self.permission_type` assigned there.
    """
    @with_new_app
    @with_new_subscribed_user
    def test_share_with_existing_user(self):
        """
        Tests sharing with an email address that is already tied to an
        existing Siphon account.
        """
        self._login()
        self.assertEqual(
            User.objects.filter(email=OTHER_USER_EMAIL).count(), 1)
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        self.assertEqual(status, 200, obj)
        self.assertTrue('invite_code' in obj)

        # Check that a permission model was created, but it is only an
        # inactive invite at this stage.
        self.assertEqual(AppPermission.objects.count(), 1)
        self.assertEqual(AppPermission.objects.filter(
            app__app_id=TEST_APP_ID,
            user__username=OTHER_USER_USERNAME,
            invite_email=OTHER_USER_EMAIL,
            permission_type=self.permission_type,
            invite_code=obj['invite_code'],
            active=False
        ).count(), 1)

    @with_new_app
    @with_new_subscribed_user
    def test_share_with_no_existing_user(self):
        """
        This is the case when the email we share with has no user
        account associated yet.
        """
        no_user_email = 'no_user_account@getsiphon.com'
        self._login()
        self.assertEqual(
            User.objects.filter(email=no_user_email).count(), 0)
        obj, status = self._share(self.permission_type, no_user_email)
        self.assertEqual(status, 200, obj)
        self.assertTrue('invite_code' in obj)

        # Should not have created a User model automatically.
        self.assertEqual(
            User.objects.filter(email=no_user_email).count(), 0)

        # Check that a permission model was created, but it is only an
        # inactive invite at this stage.
        self.assertEqual(AppPermission.objects.count(), 1)
        self.assertEqual(AppPermission.objects.filter(
            app__app_id=TEST_APP_ID,
            user=None,
            invite_email=no_user_email,
            permission_type=self.permission_type,
            invite_code=obj['invite_code'],
            active=False
        ).count(), 1)

    @with_new_app
    @with_new_subscribed_user
    def test_share_sends_email(self):
        # Do a valid share.
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        self.assertEqual(status, 200, obj)

        # Make sure an email was sent.
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [OTHER_USER_EMAIL])
        self.assertTrue(App.objects.get(app_id=TEST_APP_ID).display_name in \
            message.subject)

    @with_new_app
    @with_new_subscribed_user
    def test_share_with_bad_email(self):
        self._login()
        obj, status = self._share(self.permission_type, 'bademail')
        self.assertEqual(status, 400, obj)
        self.assertTrue('Invalid email address' in obj.get('detail', ''), obj)
        self.assertEqual(AppPermission.objects.count(), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_share_with_unknown_app(self):
        self._login()
        obj, status = self._share(self.permission_type,
            'some_email@getsiphon.com', app_id='dummy-app-id')
        self.assertEqual(status, 400, obj)
        self.assertTrue('App does not exist, or you do not own this app.' \
            in obj['detail'], obj)
        self.assertEqual(AppPermission.objects.count(), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_share_unauthenticated(self):
        obj, status = self._share(self.permission_type,
            'some_email@getsiphon.com')
        self.assertEqual(status, 302, obj)  # login redirect
        self.assertEqual(AppPermission.objects.count(), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_share_with_app_not_owned(self):
        """ App not owned by auth'd user. """
        app_id = 'some-new-app-id'
        App.objects.create(
            user=self.other_user,
            name='some-new-app',
            app_id=app_id,
            display_name='Some display name',
            base_version=BaseVersion.objects.get(name=TEST_APP_BASE_VERSION)
        )

        self._login()
        obj, status = self._share(self.permission_type,
            'some_email@getsiphon.com', app_id=app_id)
        self.assertEqual(status, 400, obj)
        self.assertTrue('App does not exist, or you do not own this app.' \
            in obj.get('detail', ''), obj)
        self.assertEqual(AppPermission.objects.count(), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_share_with_same_email_as_owner(self):
        """
        Should not be able to share to the same email address as the
        authenticated user.
        """
        self._login()
        obj, status = self._share(self.permission_type, TEST_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        self.assertTrue('You can not share an app with your own email ' \
            'address' in obj.get('detail', ''), obj)
        self.assertEqual(AppPermission.objects.count(), 0)

    @with_new_app
    @with_new_subscribed_user
    def test_share_when_already_shared_with_email(self):
        """
        Should not be able to share to the same email address multiple
        times, even if not accepted yet.
        """
        self.assertEqual(AppPermission.objects.count(), 0)

        # Do a valid share.
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        self.assertEqual(status, 200, obj)
        self.assertEqual(AppPermission.objects.filter(
            invite_email__iexact=OTHER_USER_EMAIL).count(), 1)

        # Try to do it again.
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        self.assertEqual(status, 400, obj)
        self.assertTrue('already shared' in obj.get('detail', ''), obj)
        self.assertEqual(AppPermission.objects.filter(
            invite_email__iexact=OTHER_USER_EMAIL).count(), 1)


class TestPermissionsInvitation(PermissionsTestCase):
    """
    Note: this is abstract, subclasses must also inherit TestCase and define
    their own setUp() with `self.permission_type` assigned there.
    """
    @with_new_app
    @with_new_subscribed_user
    def test_invite_acceptance(self):
        """
        For the case when invitation is sent to an already registered
        user account. This test is basically covering the entire flow.
        """
        # Share the app with a prospective user (for which a
        # User model already exists)
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        invite_code = obj['invite_code']

        # Sanity check on the permission model.
        app_permission = AppPermission.objects.get(invite_code=invite_code)
        self.assertEqual(app_permission.active, False)
        self.assertEqual(app_permission.user,
            User.objects.get(email=OTHER_USER_EMAIL))
        self.assertEqual(app_permission.invite_email, OTHER_USER_EMAIL)
        del app_permission

        # Simulate the other user clicking on the email link, while logged in.
        self._login_as_other_user()
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 200)

        # Check that the team member's User model has been assigned to the
        # AppPermission model and an aliased app exists.
        app_permission = AppPermission.objects.get(
            app__app_id=TEST_APP_ID, invite_code=invite_code)
        self.assertEqual(app_permission.active, True)
        self.assertEqual(app_permission.deleted, False)
        self.assertEqual(app_permission.user.username, OTHER_USER_USERNAME)
        self.assertNotEqual(app_permission.get_aliased_app(), None)
        self.assertNotEqual(app_permission.get_aliased_app().app_id,
            TEST_APP_ID)
        if self.permission_type == AppPermission.TYPE_TEAM_MEMBER:
            self.assertEqual(app_permission.get_aliased_app().user.username,
                OTHER_USER_USERNAME)
        else:
            self.assertEqual(app_permission.get_aliased_app().user.username,
                TEST_USER_USERNAME)

    @with_new_app
    @with_new_subscribed_user
    def test_invite_acceptance__brand_new_user(self):
        """
        For the case when an invitation is sent to an email address which
        is not currently associated with a User model.
        """
        # Send to an email address *not* tied to an existing User account.
        new_email = 'totally_new@getsiphon.com'
        self._login()
        obj, status = self._share(self.permission_type, new_email)
        invite_code = obj.get('invite_code')
        self.assertNotEqual(invite_code, None, obj)

        # Make sure no user is yet assigned to the AppPermission model.
        app_permission = AppPermission.objects.get(invite_code=invite_code)
        self.assertEqual(app_permission.active, False)
        self.assertEqual(app_permission.user, None)

        # Create the new user (a real prospective user would need to do this
        # first before getting to the acceptance page).
        new_user = User.objects.create_user('totally_new_user', new_email)
        new_user.set_password('somepass1234')
        new_user.save()

        # Login and accept the invite.
        self._login(username='totally_new_user', password='somepass1234')
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 200)

        # Make sure the User model was assigned correctly.
        perm = AppPermission.objects.get(invite_code=invite_code)
        self.assertEqual(perm.user.username, 'totally_new_user')
        self.assertEqual(perm.active, True)

    @with_new_app
    @with_new_subscribed_user
    def test_invite_accept_fails_if_not_authenticated(self):
        """
        An invitation accept link should only be reachable if logged in.
        """
        self._login()
        obj, status = self._share(self.permission_type,
            'blablabla@getsiphon.com')
        invite_code = obj.get('invite_code')
        self.assertNotEqual(invite_code, None, obj)

        # Accept while not authenticated.
        self.client.logout()
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 302, resp.content)

    @with_new_app
    @with_new_subscribed_user
    def test_invite_accept_fails_if_new_email_but_owner_user(self):
        """
        It shouldn't be possible to share with a brand new email address,
        then login with the original owner account to accept the invite.
        """
        self._login()
        obj, status = self._share(self.permission_type,
            'blablabla@getsiphon.com')
        invite_code = obj.get('invite_code')
        self.assertNotEqual(invite_code, None, obj)

        # Accept while still logged in as the original app owner.
        self._login()
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 400)
        self.assertTrue('to an app that you already own' in \
            resp.content.decode('utf-8'))

    @with_new_app
    @with_new_subscribed_user
    def test_invalid_invitation_code(self):
        self._login_as_other_user()
        resp = self._accept('bad-invite-code')
        self.assertEqual(resp.status_code, 400)
        s = resp.content.decode('utf-8')
        self.assertTrue('Unknown invite code' in s)

    @with_new_app
    @with_new_subscribed_user
    def test_already_accepted_invitation_code(self):
        # Share the app.
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        invite_code = obj['invite_code']

        # Accept the invite.
        self._login_as_other_user()
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 200)

        # Sanity check.
        self.assertEqual(AppPermission.objects.count(), 1)
        perm = AppPermission.objects.get(invite_code=invite_code)
        self.assertEqual(perm.active, True)

        # Accepting again should be idempotent.
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(AppPermission.objects.count(), 1)

    @with_new_app
    @with_new_subscribed_user
    def test_app_owner_can_not_accept_invite(self):
        # Share the app.
        self._login()
        obj, status = self._share(self.permission_type, OTHER_USER_EMAIL)
        invite_code = obj['invite_code']

        # Stay logged in as the main test user, accept as them.
        resp = self._accept(invite_code)
        self.assertEqual(resp.status_code, 400)
        s = resp.content.decode('utf-8')
        self.assertTrue('invitation is linked to a different' in s)

        # Should not have worked.
        perm = AppPermission.objects.get(invite_code=invite_code)
        self.assertNotEqual(perm.user.username, perm.app.user.username)
        self.assertEqual(perm.active, False)
