
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from siphon.web.apps.accounts.models import Token

# Create a new auth token for the user automatically when their User model is created
@receiver(post_save, sender=User)
def create_user_token(sender, instance, created, raw, **kwargs):
    if created and not raw:
        Token.objects.create(user=instance)