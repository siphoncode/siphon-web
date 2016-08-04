
import re
import time

from django.contrib.auth.models import User
from rest_framework import serializers
from siphon.web.apps.apps.models import App

def to_timestamp(dt):
    return int(time.mktime(dt.timetuple())*1000)


class AppSerializer(serializers.Serializer):
    owner = serializers.CharField() # Username of app owner
    name = serializers.CharField(max_length=100)
    app_id = serializers.CharField(max_length=64, read_only=True)
    created = serializers.DateTimeField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)

    # These are marked as read-only, but as a special case they can set with
    # a PUT request (and only the bundler is supposed to do this).
    display_name = serializers.CharField(max_length=32, read_only=True)
    base_version = serializers.CharField(max_length=32, read_only=True)
    facebook_app_id = serializers.CharField(max_length=32, read_only=True)

    def create(self, validated_data):
        user = User.objects.get(username=validated_data.get('owner'))
        app = App.objects.create(
            user=user,
            name=validated_data['name']
        )
        return app

    def validate(self, data):
        # Check that an App with the same name does not already belong to the
        # user.
        user = User.objects.get(username=data.get('owner'))
        if App.objects.filter(user=user, name=data.get('name'), deleted=False):
            raise serializers.ValidationError('App name must be unique ' \
                'for user.')
        return data

    def validate_name(self, value):
        if not re.match(r'[a-zA-Z0-9_\-]+$', value):
            raise serializers.ValidationError(
                'Siphon app names may only contain letters, numbers, ' \
                'underscores and hyphens.'
            )
        return value

    def to_representation(self, instance):
        if instance.base_version is None:
            base_version = None
        else:
            base_version = instance.base_version.name
        custom_rep = {
            'name': instance.name,
            'display_name': instance.display_name or None,
            'facebook_app_id': instance.facebook_app_id or None,
            'id': instance.app_id,
            'created': to_timestamp(instance.created), # to UNIX time
            'last_updated': to_timestamp(instance.last_updated),
            'base_version': base_version,
            'react_native_version': instance.base_version.react_native_version,
            'published': {
                'ios': False,
                'android': False
            }
        }
        return custom_rep
