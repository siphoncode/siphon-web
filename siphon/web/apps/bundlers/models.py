
from siphon.web.utils.external import make_development_handshake, \
    make_production_handshake

from django.db import models


class Bundler(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    port = models.IntegerField(default=443)

    def __str__(self):
        return '<Bundler: %s:%s>' % (self.hostname, self.port)

    def _make_url(self, action, app_id, token, signature,
                  submission_id=None, platform=None):
        url = 'https://{host}:{port}/v1/%s/%s/?handshake_token={token}&' \
              'handshake_signature={signature}' % (action, app_id)
        formatted = url.format(
            host=self.hostname,
            port=self.port,
            token=token,
            signature=signature,
        )
        if submission_id is not None:
            formatted += '&submission_id=%s' % submission_id
        if platform is not None:
            formatted += '&platform=%s' % platform
        return formatted

    def get_signed_submission_url(self, submission_id, app_id, action,
                                  platform=None):
        """ Used for production apps. """
        assert action in ('submit', 'pull')
        token, signature = make_production_handshake(action,
            submission_id, app_id)
        if action == 'submit':
            return self._make_url('submit', app_id, token, signature,
                                  platform=platform)
        elif action == 'pull':
            return self._make_url('pull', app_id, token, signature,
                submission_id=submission_id)

    def get_signed_url(self, user_id, app_id, action, platform=None):
        """
        Only used for development apps. Returns a signed URL for this
        bundler that is tied to a particular action ('push' or 'pull'),
        developer (user_id) and app (app_id).
        """
        assert action in ('push', 'pull')
        token, signature = make_development_handshake(action, user_id, app_id)
        return self._make_url(action, app_id, token, signature,
                              platform=platform)
