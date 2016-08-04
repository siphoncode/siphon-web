
import random

from django.db import models
from django.contrib.auth.models import User

from siphon.web.utils.siphon_id import generate_slug
from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer

from siphon.web.apps.apps.constants import APP_STORE_LANGUAGE_CODES
from siphon.web.apps.apps.constants import PLAY_STORE_LANGUAGE_CODES

def gen_language_choices(language_codes):
    choices = []
    for l in language_codes:
        choices.append((l.lower(), l))
    return tuple(choices)

APP_STORE_LANGUAGE_CHOICES = gen_language_choices(APP_STORE_LANGUAGE_CODES)
PLAY_STORE_LANGUAGE_CHOICES = gen_language_choices(PLAY_STORE_LANGUAGE_CODES)
ICON_SIZE_CHOICES = ((512, 512), (1024, 1024))
ICON_FORMAT_CHOICES = (('png', 'PNG'),)
PLATFORMS = (('ios', 'iOS'), ('android', 'Android'))

class BaseVersion(models.Model):
    name = models.CharField(max_length=32,
        help_text='The base_version itself e.g. "0.1"')
    react_native_version = models.CharField(max_length=32,
        help_text='React Native release that this base_version is tied to ' \
        'e.g. "0.18.0"')
    comment = models.TextField(blank=True,
        help_text='User-facing notes about which native modules are ' \
        'available in this base_version and any other useful information.')
    latest = models.BooleanField(default=False,
        help_text='Signals the currently active base_version that newly ' \
        'created Siphon apps will be assigned automatically. Note that ' \
        'setting this flag to True will turn it off for the currently ' \
        'active model so that this is the only one.')

    def __str__(self):
        s = self.name
        if self.latest:
            s += ' (latest)'
        return s

    @staticmethod
    def get_latest():
        return BaseVersion.objects.get(latest=True)

    def save(self, *args, **kwargs):
        # On save, if latest=True on this model then we turn it off
        # for any other models, i.e. the switch is automatic.
        if self.latest is True:
            for obj in BaseVersion.objects.filter(latest=True):
                if obj != self:
                    obj.latest = False
                    obj.save()
        super(BaseVersion, self).save(*args, **kwargs)

class App(models.Model):
    user = models.ForeignKey(User, related_name='apps')
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=32, blank=True)
    app_id = models.CharField(max_length=64, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    # These are assigned on app creation.
    bundler = models.ForeignKey(Bundler, related_name='apps')
    streamer = models.ForeignKey(Streamer, related_name='apps')

    # This corresponds to "base_version" in Siphonfile and should be
    # updated on every push.
    base_version = models.ForeignKey(BaseVersion)

    # Corresponds the app ID set at FB's developer portal.
    facebook_app_id = models.CharField(max_length=32, blank=True)

    # Publishing metadata fields
    app_store_name = models.CharField(max_length=255, blank=True)
    app_store_language = models.CharField(max_length=7, blank=True,
                                          choices=APP_STORE_LANGUAGE_CHOICES)
    play_store_name = models.CharField(max_length=30, blank=True)
    play_store_language = models.CharField(max_length=7, blank=True,
                                           choices=PLAY_STORE_LANGUAGE_CHOICES)

    # Lazily created for "siphon share".
    beta_testing_alias = models.OneToOneField('self', models.PROTECT,
        null=True, blank=True, related_name='master_app')

    def __str__(self):
        return u'<App app_id=%s, name="%s" user=%s base_version=%s>' % (
            self.app_id, self.name, self.user.username,
            self.base_version.name)

    def save(self, *args, **kwargs):
        if not self.app_id:
            self.app_id = self._generate_id()
        if not self.bundler_id:
            self._assign_bundler()
        if not self.streamer_id:
            self._assign_streamer()
        if not self.base_version_id:
            self.base_version = BaseVersion.get_latest()
        return super(App, self).save(*args, **kwargs)

    def _assign_bundler(self):
        """ Randomly assigns this app to a bundler server. """
        bundlers = Bundler.objects.all()
        assert len(bundlers) > 0
        self.bundler = random.choice(bundlers)

    def _assign_streamer(self):
        """ Randomly assigns this app to a streamer server. """
        streamers = Streamer.objects.all()
        assert len(streamers) > 0
        self.streamer = random.choice(streamers)

    def duplicate(self, user=None):
        assert self.deleted is False
        if user is None:
            user = self.user
        return App(
            user=user,
            name=self.name,
            display_name=self.display_name,
            base_version=self.base_version
        )

    def is_beta_testing_alias(self):
        try:
            if self.master_app:
                return True
        except App.DoesNotExist:
            pass
        return False

    def get_beta_testing_alias(self):
        if self.is_beta_testing_alias():
            return None
        # Lazily copy an alias on demand.
        if not self.beta_testing_alias:
            a = self.duplicate()
            a.save()
            self.beta_testing_alias = a
            self.save()
        return self.beta_testing_alias

    def get_bundler_url(self, action, platform=None):
        assert action in ('push', 'pull')
        assert platform in (None, 'ios', 'android')
        return self.bundler.get_signed_url(
            self.user.username,
            self.app_id,
            action,
            platform,
        )

    def get_bundler_url_for_submission(self, action, submission_id,
                                       platform=None):
        assert action in ('submit', 'pull')
        return self.bundler.get_signed_submission_url(
            submission_id, self.app_id, action, platform=platform)

    def get_streamer_url(self, stream_type):
        return self.streamer.get_signed_url(
            self.user.username,
            self.app_id,
            stream_type
        )

    def _generate_id(self):
        new_id = generate_slug()
        # Check the id is not already associated with another App
        # (highly unlikely)
        while App.objects.filter(app_id=new_id).exists():
            new_id = generate_slug()
        return new_id

class AppIcon(models.Model):
    """
    AppIcon model for storing app icon metadata
    """
    app = models.ForeignKey(App, related_name='icons')
    name = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORMS)
    height = models.IntegerField(choices=ICON_SIZE_CHOICES)
    width = models.IntegerField(choices=ICON_SIZE_CHOICES)
    image_format = models.CharField(max_length=100,
                                    choices=ICON_FORMAT_CHOICES)
