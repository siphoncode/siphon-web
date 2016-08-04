
import os
from siphon.web.settings import BASE_DIR

DEBUG = True

# For generating handshake tokens
HANDSHAKE_PRIVATE_KEY = os.path.join(BASE_DIR,
    '../deployment/keys/handshake/handshake.pem')
HANDSHAKE_PUBLIC_KEY = os.path.join(BASE_DIR,
    '../deployment/keys/handshake/handshake.pub')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'siphon_web_local',
        'HOST': 'localhost',
        'PORT': 5432
    }
}

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO'
        }
    }
}

# So that we don't need to use collectstatic locally.
STATIC_ROOT = os.path.join(BASE_DIR, '../static')
STATICFILES_DIRS = ()
COMPRESS_OUTPUT_DIR = '.cache'

# Send emails to console instead of Mailgun
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Chargebee
CHARGEBEE_API_KEY = 'CHANGEME'
CHARGEBEE_SITE = 'https://siphon-test.chargebee.com'
