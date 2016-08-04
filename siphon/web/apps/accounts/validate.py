"""
Validation logic shared between the API serializer and register/login views.
"""

import re

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

MIN_PASSWORD_LENGTH = 6
RE_USERNAME = re.compile(r'[\w.+-]+$')

# Define messages like this so we can check for them in tests
MSG_NAME_REQUIRED = 'Your full name is required.'
MSG_EMAIL_TAKEN = 'Sorry, this email is already associated with another ' \
    'username.'
MSG_PASSWORD_INVALID = 'Your password must contain at least ' \
    '%d characters.' % MIN_PASSWORD_LENGTH
MSG_PASSWORD_UNCONFIRMED = 'The password confirmation does not match.'
MSG_USERNAME_REQUIRED = 'Please choose a username.'
MSG_USERNAME_INVALID = 'Username may only consist of letters, numbers, or ' \
    'the characters ., + , - '
MSG_USERNAME_TAKEN = 'Sorry, this username is taken.'


def name(first_name, last_name):
    for value in (first_name, last_name):
        if not isinstance(value, str) or len(value) < 1:
            raise ValidationError(MSG_NAME_REQUIRED)
    return value

def username(value):
    if not isinstance(value, str) or len(value) < 1:
        raise ValidationError(MSG_USERNAME_REQUIRED)
    if not RE_USERNAME.match(value):
        raise ValidationError(MSG_USERNAME_INVALID)
    # Make sure username does already exist
    if User.objects.filter(username__iexact=value.lower()).count() > 0:
        raise ValidationError(MSG_USERNAME_TAKEN)
    return value

def email(value):
    # Make sure email does already exist
    if User.objects.filter(email__iexact=value.lower()).count() > 0:
        raise ValidationError(MSG_EMAIL_TAKEN)
    return validate_email(value)

def password(value, confirm_value=None):
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(MSG_PASSWORD_INVALID)
    if confirm_value is not None and value != confirm_value:
        raise ValidationError(MSG_PASSWORD_UNCONFIRMED)
    return value
