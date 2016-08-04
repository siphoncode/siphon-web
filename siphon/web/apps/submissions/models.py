
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string

from siphon.web.apps.apps.models import App, BaseVersion
from siphon.web.utils.siphon_id import generate_slug

class Submission(models.Model):
    STATUS_PROCESSING = 'processing'
    STATUS_AWAITING_RELEASE = 'awaiting_release'
    STATUS_RELEASED = 'released'
    STATUSES = (
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_AWAITING_RELEASE, 'Awaiting Release'),
        (STATUS_RELEASED, 'Released')
    )
    PLATFORMS = (('ios', 'iOS'), ('android', 'Android'))

    submission_id = models.CharField(max_length=64, primary_key=True)
    app = models.ForeignKey(App)
    user = models.ForeignKey(User)
    base_version = models.ForeignKey(BaseVersion)
    display_name = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=20, choices=STATUSES)
    is_failed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False, help_text='Signals ' \
        'whether a submission is ready for clients to upgrade to.')

    # Platform info
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    platform_username = models.CharField(max_length=255, blank=True)
    platform_password = models.CharField(max_length=255, blank=True)  # temp

    def save(self, *args, **kwargs):
        # Check if the status has changed. If the submission has just
        # been created with status processing or the status has changed
        # to awaiting release, send an email to the user.
        from_field = 'Siphon <hello@getsiphon.com>'
        user_email = self.app.user.email

        if not self.submission_id:
            self.submission_id = Submission.new_id()

        try:
            orig = Submission.objects.get(submission_id=self.submission_id)
            if orig.status == Submission.STATUS_PROCESSING and \
            self.status == Submission.STATUS_AWAITING_RELEASE:
                # The submission status has been updated from STATUS_PROCESSING
                # to STATUS_AWAITING_RELEASE so send email
                subject = '[Siphon] Your submission is awaiting release'
                msg_path = 'emails/submissions/' \
                           'awaiting_release_%s.txt' % self.platform
                message = render_to_string(msg_path)
                send_mail(subject, message, from_field, [user_email])
        except Submission.DoesNotExist:
            if self.status == Submission.STATUS_PROCESSING:
                # The submission has just been created so send processing email
                subject = '[Siphon] Your submission is processing'
                msg_path = 'emails/submissions/' \
                           'processing_%s.txt' % self.platform
                message = render_to_string(msg_path)
                send_mail(subject, message, from_field, [user_email])

        return super(Submission, self).save(*args, **kwargs)

    @staticmethod
    def new_id():
        s = generate_slug()
        while Submission.objects.filter(submission_id=s).exists():
            s = generate_slug()
        return s

    @staticmethod
    def latest_submission_for_app(app, platform=None):
        """
        Returns the newest submission for a given app, including inactive ones.

        If a platform is provided, then return the latest submision for that
        app for the given platform.
        """
        if not platform:
            return (
                Submission.objects.filter(app=app).order_by('-created').first()
            )
        else:
            return (
                Submission.objects.filter(app=app, platform=platform)
                .order_by('-created')
                .first()
            )

    @staticmethod
    def app_requires_hard_update(app, platform=None):
        """
        Returns True if this app has either (A) never been submitted before
        or (B) changed since the last submission such that a hard update
        will be required. A hard update means we need to submit a new
        binary to the App Store for approval.
        """
        submission = Submission.latest_submission_for_app(app, platform)
        if submission is None:
            return True
        elif submission.base_version != app.base_version:
            return True
        elif submission.display_name != app.display_name:
            return True
        else:
            return False

    def __str__(self):
        return '<Submission id=%s, user=%s, app="%s", status=%s>' % (
            self.submission_id, self.user.username, self.app.display_name,
            self.status)

    def get_latest_active(self):
        """
        Given this submission, returns the latest active submission for this
        app, using `Submission.created` for ordering. This method may return
        the same submission, or None.
        """
        return (
            Submission.objects.filter(
                app=self.app, is_active=True, platform=self.platform)
            .order_by('-created')
            .first()
        )
