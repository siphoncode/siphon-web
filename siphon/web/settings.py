
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGEME'
raise Exception('Need to set a SECRET_KEY!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

SERVER_EMAIL = 'postmaster@getsiphon.com' # default can cause issues

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Siphon
    'siphon.web.apps.core',
    'siphon.web.apps.accounts',
    'siphon.web.apps.apps',
    'siphon.web.apps.bundlers',
    'siphon.web.apps.streamers',
    'siphon.web.apps.docs',
    'siphon.web.apps.subscriptions',
    'siphon.web.apps.submissions',
    'siphon.web.apps.analytics',
    'siphon.web.apps.permissions',

    # Third-party
    'rest_framework',
    'compressor',
    'drip'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # These need to go before `CsrfViewMiddleware` because they turn
    # off CSRF checking in certain cases.
    'siphon.web.apps.accounts.middleware.TokenAuthMiddleware',
    'siphon.web.apps.accounts.middleware.HandshakeAuthMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'siphon.web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Siphon
                'siphon.web.utils.context_processors.environment',
            ],
        },
    },
]

WSGI_APPLICATION = 'siphon.web.wsgi.application'

LOGIN_REDIRECT_URL = 'static:dashboard'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '../.static') # collectstatic dumps here

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '../static'), # source of our static files
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
)

SIPHON_BACKDOOR_USER = 'siphon_backdoor'

# Security
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 999999999, # unlimited for now
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

## django-libsass

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

LIBSASS_OUTPUT_STYLE = 'compressed'

## django-drip

DRIP_FROM_EMAIL = 'Siphon <hello@getsiphon.com>'


if os.environ.get('SIPHON_ENV') == 'production':
    print('[settings_production]')
    from siphon.web.settings_production import *
elif os.environ.get('SIPHON_ENV') == 'staging':
    print('[settings_staging]')
    from siphon.web.settings_staging import *
elif os.environ.get('SIPHON_ENV') == 'dev':
    print('[settings_local]')
    from siphon.web.settings_local import *
else:
    print('SIPHON_ENV must be set.')
    sys.exit(1)
