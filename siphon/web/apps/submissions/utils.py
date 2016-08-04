
class InvalidAppException(Exception):
    def __init__(self, msg):
        self.msg = msg

def validate_app(app, platform):
    """
    Takes an app instance and checks that we have all the info we need
    to publish it for the specified platform. Raises an InvalidAppException
    if the app is invalid.
    """
    assert(platform in ['ios', 'android'])
    if not app.display_name:
        raise InvalidAppException('Before publishing ' \
            'this app you must add a ' \
            '"display_name" to your Siphonfile. Read more here: ' \
            'https://getsiphon.com/docs/faq/#display-name')

    if platform == 'ios':
        if not app.app_store_name:
            raise InvalidAppException('Before publishing this app to ' \
            'the App Store you must add a store_name to your Siphonfile for ' \
            'the iOS platform.')

        if not app.app_store_language:
            raise InvalidAppException('Before publishing this app to ' \
            'the App Store you must add a language to your Siphonfile for ' \
            'the iOS platform.')

        if not app.icons.filter(platform='ios'):
            raise InvalidAppException('Before publishing this app to ' \
            'the App Store you must add an icon to the publish/ios/icons ' \
            'directory in you app directory.')
    else:
        # We're validating the app to be published to the Play Store
        if not app.play_store_name:
            raise InvalidAppException('Before publishing this app to ' \
            'the Play Store you must add a store_name to your Siphonfile for ' \
            'the Android platform.')

        if not app.play_store_language:
            raise InvalidAppException('Before publishing this app to ' \
            'the Play Store you must add a language to your Siphonfile for ' \
            'the Android platform.')

        if not app.icons.filter(platform='android'):
            raise InvalidAppException('Before publishing this app to ' \
            'the Play Store you must add an icon to the ' \
            ' publish/android/icons directory in you app directory.')
