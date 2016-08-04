
import os

DEBUG = False

ADMINS = (
    ('Change Me', 'todo@getsiphon.com'),
)

# This protection is handled in nginx.conf
ALLOWED_HOSTS = ['*']

# For generating handshake tokens
HANDSHAKE_PRIVATE_KEY = '/code/.keys/handshake/handshake.pem'
HANDSHAKE_PUBLIC_KEY = '/code/.keys/handshake/handshake.pub'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_WEB_ENV_POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_WEB_ENV_POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_WEB_ENV_POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_WEB_PORT_5432_TCP_ADDR'),
        'PORT': 5432
    }
}

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/volumes/logs/django.log'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console', 'mail_admins'],
            'level': 'INFO'
        }
    }
}

## Mailgun

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
MAILGUN_ACCESS_KEY = 'CHANGEME'
MAILGUN_SERVER_NAME = 'mg.getsiphon.com'

# Chargebee
CHARGEBEE_API_KEY = 'CHANGEME'
CHARGEBEE_SITE = 'https://siphon.chargebee.com'
