
from django.dispatch import receiver
from django.db.models.signals import post_save

from siphon.web.apps.apps.models import App
from siphon.web.apps.permissions.models import AppPermission
from siphon.web.utils.rabbitmq import post_notification


@receiver(post_save, sender=App)
def send_app_notification(sender, instance, created, raw, **kwargs):
    """ Post a RabbitMQ notification when an app is created/updated. """
    app = instance
    usernames = [app.user.username]

    # By default we just post a notification for the app owner, but if this
    # is a beta testing alias then we notify any active beta testers too.
    if app.is_beta_testing_alias():
        usernames += [user.username for user in \
            AppPermission.get_beta_testers(app.master_app)]

    for username in usernames:
        post_notification({
            'type': 'new_app' if created else 'app_updated',
            'app_id': app.app_id,
            'user_id': username
        })
