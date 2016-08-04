
# We use production settings, but override certain sensitive settings
from siphon.web.settings_production import *

# Chargebee
CHARGEBEE_API_KEY = 'CHANGEME'
CHARGEBEE_SITE = 'https://siphon-test.chargebee.com'

# Emails
EMAIL_SUBJECT_PREFIX = '[Django] [STAGING] '
