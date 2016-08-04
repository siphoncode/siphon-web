
import re

from rest_framework import serializers
from rest_framework import validators
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from siphon.web.apps.accounts import validate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {
            'username': {'validators': [
                validators.UniqueValidator(queryset=User.objects.all())
            ]},
            'email': {'validators': [
                validators.UniqueValidator(queryset=User.objects.all())
            ]},
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        user = User.objects.create_user(username, email, password)
        return user

    def validate_username(self, value):
        try:
            validate.username(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_email(self, value):
        try:
            validate.email(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_password(self, value):
        try:
            validate.password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value
