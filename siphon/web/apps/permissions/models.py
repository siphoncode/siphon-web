
import uuid

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse

from siphon.web.apps.apps.models import App
from siphon.web.apps.permissions import AppSharingException


def make_invite_code():
    return str(uuid.uuid4())


class AppPermission(models.Model):
    TYPE_TEAM_MEMBER = 'team-member'
    TYPE_BETA_TESTER = 'beta-tester'
    PERMISSION_TYPES = (
        (TYPE_TEAM_MEMBER, 'Team member'),
        (TYPE_BETA_TESTER, 'Beta tester')
    )

    app = models.ForeignKey(App, related_name='app_permissions')
    user = models.ForeignKey(User, blank=True, null=True)
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    active = models.BooleanField(default=False)  # set when invite is accepted

    invite_email = models.EmailField(unique=True)
    invite_code = models.CharField(max_length=255, unique=True,
        default=make_invite_code)

    # This is only set for the 'team-member' type, after an invitation
    # has been accepted.
    aliased_app = models.OneToOneField(App, blank=True, null=True,
        related_name='app_permission')

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        username = None
        if self.user:
            username = self.user.username
        return '<AppPermission: type=%s, app=%s, user=%s, active=%s, ' \
            'deleted=%s>' % (self.permission_type, self.app.app_id, username,
            self.active, self.deleted)

    def get_aliased_app(self):
        """
        This should always be used instead of retrieving
        `AppPermission.aliased_app` directly. For team sharing permissions it
        returns `AppPermission.aliased_app`, for beta testing permissions
        it returns `App.beta_testing_alias`.
        """
        if self.permission_type == self.TYPE_TEAM_MEMBER:
            return self.aliased_app
        elif self.permission_type == self.TYPE_BETA_TESTER:
            # Cache buster.
            app = App.objects.get(app_id=self.app_id)
            return app.get_beta_testing_alias()
        else:
            raise RuntimeError('Unexpected permission type: %s' %
                self.permission_type)

    def activate(self, user):
        assert self.active is False
        assert self.deleted is False
        assert self.permission_type in (self.TYPE_TEAM_MEMBER,
            self.TYPE_BETA_TESTER)

        if self.permission_type == self.TYPE_TEAM_MEMBER:
            # For team-member type, we create the aliased app at the time
            # of activation.
            aliased_app = self.app.duplicate(user=user)
            aliased_app.save()
            self.aliased_app = aliased_app

        self.user = user
        self.active = True
        self.save()

    def send_invite_email(self):
        assert not self.active

        # Use the display name if we can.
        if self.app.display_name:
            name = self.app.display_name
        else:
            name = self.app.name

        accept_url = 'https://getsiphon.com%s' % \
            reverse('permissions:accept-invite',
                kwargs={'invite_code': self.invite_code})

        # Prepare the body.
        if self.permission_type == AppPermission.TYPE_TEAM_MEMBER:
            subject = '[Siphon] Invitation to collaborate on "%s"' % name
            message = render_to_string('emails/share_team_member_invite.txt', {
                'team_leader_username': self.app.user.username,
                'app_name': name,
                'accept_url': accept_url,
                'team_sharing_url': 'https://getsiphon.com%s' % \
                reverse('docs:team-sharing')
            })
        elif self.permission_type == AppPermission.TYPE_BETA_TESTER:
            subject = '[Siphon] Invitation to beta test "%s"' % name
            message = render_to_string('emails/share_beta_tester_invite.txt', {
                'owner_username': self.app.user.username,
                'app_name': name,
                'accept_url': accept_url
            })
        else:
            raise RuntimeError('Not implemented: %s' % self.permission_type)

        # Send the email.
        from_field = 'Siphon <hello@getsiphon.com>'
        send_mail(subject, message, from_field, [self.invite_email])

    @staticmethod
    def notify_beta_testers(app):
        for beta_user in AppPermission.get_beta_testers(app):
            AppPermission.notify_beta_tester(app, beta_user)

    @staticmethod
    def notify_beta_tester(app, beta_user):
        # Use the display name if we can.
        if app.display_name:
            name = app.display_name
        else:
            name = app.name

        # Prepare the body.
        subject = '[Siphon] There is an update available for "%s"' % name
        message = render_to_string('emails/share_beta_tester_update.txt', {
            'owner_username': app.user.username,
            'app_name': name
        })

        # Send the email.
        from_field = 'Siphon <hello@getsiphon.com>'
        send_mail(subject, message, from_field, [beta_user.email])

    @staticmethod
    def get_beta_testers(app):
        return [perm.user for perm in AppPermission.objects.filter(
            permission_type=AppPermission.TYPE_BETA_TESTER,
            app=app,
            app__deleted=False,
            active=True,
            deleted=False
        )]

    @staticmethod
    def get_permission_for_beta_tester(app, beta_user):
        try:
            return AppPermission.objects.get(
                permission_type=AppPermission.TYPE_BETA_TESTER,
                user=beta_user,
                app=app.master_app,
                active=True,
                deleted=False
            )
        except AppPermission.DoesNotExist:
            return None

    @staticmethod
    def user_is_beta_tester(app, beta_user):
        if not app.is_beta_testing_alias():
            return False
        perm = AppPermission.get_permission_for_beta_tester(app, beta_user)
        return perm is not None

    @staticmethod
    def get_team_member_alias(app, team_user):
        try:
            app_permission = AppPermission.objects.get(
                permission_type=AppPermission.TYPE_TEAM_MEMBER,
                user=team_user,
                app=app,
                active=True,
                deleted=False
            )
            return app_permission.get_aliased_app()
        except AppPermission.DoesNotExist:
            return None

    @staticmethod
    def create_and_send_invite(permission_type, app, email):
        email = email.lower()

        if permission_type not in (AppPermission.TYPE_TEAM_MEMBER, \
        AppPermission.TYPE_BETA_TESTER):
            raise AppSharingException('Invalid permission type: %s' %
                permission_type)

        # Can not share with yourself.
        if email == app.user.email.lower():
            raise AppSharingException('You can not share an app with your ' \
                'own email address.')

        # Can not share when an email that has already been shared with.
        qs = AppPermission.objects.filter(invite_email__iexact=email)
        if qs.count() > 0:
            raise AppSharingException('Sorry, this app was already shared ' \
                'with the email address that you provided.')

        # Create the placeholder permission model, but don't activate it yet.
        app_permission = AppPermission(
            app=app,
            invite_email=email,
            permission_type=permission_type
        )
        try:
            user = User.objects.get(email__iexact=email)
            app_permission.user = user
        except User.DoesNotExist:
            pass

        # Only persist once the email has sent.
        app_permission.send_invite_email()
        app_permission.save()
        return app_permission
