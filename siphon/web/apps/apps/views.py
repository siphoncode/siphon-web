
import json

from django.conf import settings

from siphon.web.utils import make_error
from siphon.web.apps.apps.constants import APP_STORE_LANGUAGE_CODES
from siphon.web.apps.apps.constants import PLAY_STORE_LANGUAGE_CODES, APP_ICONS
from siphon.web.apps.apps.models import App, AppIcon, BaseVersion
from siphon.web.apps.apps.serializers import AppSerializer
from siphon.web.apps.submissions.models import Submission
from siphon.web.apps.permissions.models import AppPermission

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import MethodNotAllowed, NotFound, ParseError
from rest_framework import generics
from rest_framework import mixins

class AppList(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AppSerializer

    def get_queryset(self):
        user = self.request.user
        if user and user.username == settings.SIPHON_BACKDOOR_USER:
            return App.objects.filter(deleted=False).order_by('-created')

        # Default list (make sure no beta testing aliases owned by the user
        # are returned).
        qs = App.objects.filter(
            user=user,
            deleted=False,
            master_app=None
        )

        # Beta testers should see aliased apps in their list too.
        app_permissions = AppPermission.objects.filter(
            permission_type=AppPermission.TYPE_BETA_TESTER,
            user=user,
            active=True,
            deleted=False,
            app__deleted=False
        )
        beta_app_ids = [p.get_aliased_app().app_id for p in app_permissions]
        beta_apps = App.objects.filter(app_id__in=beta_app_ids)
        qs = qs | beta_apps

        return qs

    def _get_individual_app(self, request, app_id):
        try:
            app = App.objects.get(app_id=app_id, deleted=False)
        except App.DoesNotExist:
            raise NotFound()

        # Deal with shared apps.
        if app.user != request.user:
            team_alias_app = AppPermission.get_team_member_alias(app,
                request.user)
            if team_alias_app:
                app = team_alias_app  # we will return alias app info.
            elif not AppPermission.user_is_beta_tester(app, request.user):
                raise NotFound()

        serializer = AppSerializer(app)
        return Response(serializer.to_representation(app))

    def get(self, request, app_id=None):
        if app_id:
            return self._get_individual_app(request, app_id)
        else:
            return self.list(request)

    def post(self, request, app_id=None):
        if app_id is not None:
            raise MethodNotAllowed('POST')  # can't POST a list of apps
        data = dict(request.data.items())  # removes rest-framework weirdness
        data['owner'] = request.user.username
        serializer = AppSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            app = serializer.save()
            return Response(serializer.to_representation(app), status=201)

    def delete(self, request, app_id=None):
        if app_id is None:
            raise MethodNotAllowed('DELETE')  # can't DELETE a list of apps
        try:
            app = App.objects.get(app_id=app_id)
        except App.DoesNotExist:
            raise NotFound()

        if app.user != request.user:
            if AppPermission.user_is_beta_tester(app, request.user):
                # Special case: if a beta tester tries to delete an app
                # from their dashboard, we mark their AppPermission model
                # as deleted instead, so they no longer see the alias.
                app_permission = AppPermission.get_permission_for_beta_tester(
                    app, request.user)
                app_permission.deleted = True
                app_permission.save()
                return Response()
            else:
                raise NotFound()

        if app.user == request.user and app.is_beta_testing_alias():
            return make_error('App owner can not delete a beta testing app.')

        # If there exist one-or-more submissions (i.e. invocations of
        # "siphon publish") for this app then we should not allow it
        # to be deleted.
        if Submission.objects.filter(app_id=app.app_id).count() > 0:
            msg = 'You are trying to delete an app that has been published. ' \
                'Please contact us if you would like to remove it: ' \
                'hello@getsiphon.com'
            return make_error(msg)
        # Otherwise, go ahead and mark it as deleted.
        app.deleted = True
        app.save()
        return Response()

    def put(self, request, app_id=None):
        if app_id is None:
            raise MethodNotAllowed('PUT')  # can't PUT to a list of apps
        # Try to retrieve the app
        qs = App.objects.filter(user=self.request.user, app_id=app_id,
            deleted=False)
        if len(qs) < 1:
            raise NotFound()
        app = qs[0]

        if app.is_beta_testing_alias():
            AppPermission.notify_beta_testers(app.master_app)

        # Validate and set the BaseVersion model associated with this app.
        if 'base_version' in request.data:
            bv = request.data['base_version']
            if not bv:
                raise ParseError('Expected base_version.')
            try:
                base_version = BaseVersion.objects.get(name=bv)
            except BaseVersion.DoesNotExist:
                raise ParseError('Unknown base_version.')
            app.base_version = base_version

        # Validate and set optional fields if they are given
        display_name = request.data.get('display_name')
        if isinstance(display_name, str):
            # Only restriction we place is length, any characters are probably
            # valid here (e.g. Chinese characters) but whether they get through
            # the iOS approval process is a seperate issue.
            if len(display_name) > 32:
                raise ParseError('Display name is maximum 32 characters.')
            app.display_name = display_name

        facebook_app_id = request.data.get('facebook_app_id')
        if isinstance(facebook_app_id, str):
            if len(facebook_app_id) > 32:
                raise ParseError('Facebook app ID is maximum 32 characters.')
            app.facebook_app_id = facebook_app_id

        app_store_name = request.data.get('app_store_name')
        if isinstance(app_store_name, str):
            if len(app_store_name) > 255:
                raise ParseError('App Store Name is maximum 255 characters.')
            app.app_store_name = app_store_name

        play_store_name = request.data.get('play_store_name')
        if isinstance(play_store_name, str):
            if len(play_store_name) > 30:
                raise ParseError('App Store Name is maximum 30 characters.')
            app.play_store_name = play_store_name

        app_store_language = request.data.get('app_store_language')
        if isinstance(app_store_language, str):
            if app_store_language and app_store_language.lower() not in \
                    (c.lower() for c in APP_STORE_LANGUAGE_CODES):
                raise ParseError('Invalid App Store language code.')
            app.app_store_language = app_store_language.lower()

        play_store_language = request.data.get('play_store_language')
        if isinstance(play_store_language, str):
            if play_store_language and play_store_language.lower() not in \
                    (c.lower() for c in PLAY_STORE_LANGUAGE_CODES):
                raise ParseError('Invalid Play Store language code.')
            app.play_store_language = play_store_language.lower()

        # Check that icons have the expected properties
        icons = request.data.get('icons')
        if isinstance(icons, str):
            icons = json.loads(icons)
        if isinstance(icons, list):
            # Keep track of the new icons we wish to add
            new_icons = []
            for user_ic in icons:
                platform = user_ic.get('platform')
                image_format = user_ic.get('image_format')
                # The following shouldn't happen, but check just in case
                # (these are checked by the bundler when extracting
                # icons from the user's publish directory)
                if platform not in ['ios', 'android']:
                    raise ParseError('Invalid platform: %s' % platform)
                if image_format != 'png':
                    raise ParseError('Unsupported icon format: %s. Icons ' \
                                     'must use the PNG file format.' \
                                    % image_format)

                name = user_ic.get('name')
                height = user_ic.get('height')
                width = user_ic.get('width')

                matching_app = False
                for expected_icon in APP_ICONS:
                    if name == expected_icon['name'] and \
                            platform == expected_icon['platform']:
                        # The name is a valid one. Check the corresponding
                        # dimensions
                        expected_height = expected_icon['height']
                        expected_width = expected_icon['width']
                        if height != expected_height or \
                                width != expected_width:
                            raise ParseError('Invalid dimensions for icon %s.' \
                                  'Expected %sx%s pixels.' \
                                  % (name, expected_width, expected_height))
                        # The icon is OK
                        new_icons.append(AppIcon(app=app,
                            name=name,
                            platform=platform,
                            height=height,
                            width=width,
                            image_format=image_format))
                        matching_app = True
                        break
                if not matching_app:
                    raise ParseError('Unrecognized icon: %s.%s' % (name,
                                                                 image_format))

            # All the icons are valid so remove old icons and replace
            # with new ones
            app.icons.all().delete()
            for icon in new_icons:
                icon.save()

        app.save()
        return Response()
