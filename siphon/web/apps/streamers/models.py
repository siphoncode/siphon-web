
from django.db import models
from siphon.web.utils.external import make_development_handshake


class Streamer(models.Model):
    STREAM_TYPE_NOTIFICATIONS = 'notifications'
    STREAM_TYPE_LOG_READER = 'log_reader'
    STREAM_TYPE_LOG_WRITER = 'log_writer'
    STREAM_TYPES = (STREAM_TYPE_NOTIFICATIONS, STREAM_TYPE_LOG_READER,
        STREAM_TYPE_LOG_WRITER)

    hostname = models.CharField(max_length=255, unique=True)
    port = models.IntegerField(default=443)

    def __str__(self):
        return '<Streamer: %s:%s>' % (self.hostname, self.port)

    def get_signed_url(self, user_id, app_id, stream_type):
        assert stream_type in self.STREAM_TYPES
        url = 'wss://{host}:{port}/v1/streams/?type={stream_type}' \
              '&handshake_token={token}&handshake_signature={signature}' \
              '&app_id={app_id}'
        token, signature = make_development_handshake(None, user_id, app_id)
        return url.format(
            host=self.hostname,
            port=self.port,
            stream_type=stream_type,
            app_id=app_id,
            token=token,
            signature=signature
        )
