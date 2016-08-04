
from django.core.exceptions import ValidationError

def validate_password(password):
    minimum_length_validator(password)
    return password

def minimum_length_validator(password, min_length=6):
    if len(password) < min_length:
        raise ValidationError('This password must contain at least %d characters.' % min_length)
    return password
