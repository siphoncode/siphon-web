
from django.contrib.auth.models import User
from django.db import models
from siphon.web.utils.siphon_id import generate_id


class Token(models.Model):
    user = models.OneToOneField(User, related_name='auth_token')
    key = models.CharField(max_length=64, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self):
        key = generate_id()
        # We want the key to be unique (we identify the user based on it)
        while Token.objects.filter(key=key).exists():
            key = generate_id()
        return key


class Invitation(models.Model):
    user = models.OneToOneField(User, blank=True, null=True)
    code = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return '<Invitation user=%s code=%s>' % (self.user, self.code)
