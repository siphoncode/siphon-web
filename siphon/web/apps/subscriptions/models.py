
from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    INTERVALS = (('monthly', 'Billed monthly'), ('yearly', 'Billed yearly'))

    name = models.CharField(max_length=255, unique=True) # user-facing
    plan_id = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True) # any extra internal notes here
    interval = models.CharField(max_length=20, choices=INTERVALS)

    # Allowances
    seats = models.PositiveIntegerField(
        help_text='Number of developer seats.')
    monthly_active_users = models.PositiveIntegerField(
        help_text='A value of zero value means unlimited.')
    max_app_size = models.PositiveIntegerField(
        help_text='Maximum app size in bytes. A value of zero means ' \
        'unlimited.')
    priority_support = models.BooleanField()
    team_sharing = models.BooleanField(default=False)
    beta_tester_sharing = models.BooleanField(default=True)

    def __str__(self):
        return self.plan_id


class Subscription(models.Model):
    user = models.OneToOneField(User, related_name='paid_subscription')
    plan = models.ForeignKey(Plan, related_name='subscriptions')
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    chargebee_id = models.CharField(max_length=255)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '<Subscription: %s | user=%s, active=%s, cancelled=%s>' % (
            self.plan.plan_id, self.user.username, self.active,
            self.cancelled)

    @staticmethod
    def user_has_valid_subscription(user):
        try:
            subscription = Subscription.objects.get(user=user)
        except Subscription.DoesNotExist:
            return False
        return subscription.active is True

class ChargebeeEvent(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    raw_content = models.TextField() # JSON dump

    def __str__(self):
        return '<ChargebeeEvent: %s | created=%s>' % (self.name, self.created)
