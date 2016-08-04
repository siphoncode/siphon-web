
from django.contrib.auth.models import User

from siphon.web.apps.apps.models import App, AppIcon, BaseVersion
from siphon.web.apps.bundlers.models import Bundler
from siphon.web.apps.streamers.models import Streamer
from siphon.web.apps.subscriptions.models import Plan, Subscription
from siphon.web.apps.submissions.models import Submission

TEST_USER_USERNAME = 'valid_name1234'
TEST_USER_EMAIL = 'valid@domain.com'
TEST_USER_PASSWORD = 'valid1234'

TEST_APP_NAME = 'TestApp'
TEST_APP_ID = 'my-test-app'
TEST_APP_BASE_VERSION = '0.5'
TEST_APP_REACT_NATIVE_VERSION = '0.22.2'
TEST_APP_DISPLAY_NAME = 'My Test App'
TEST_APP_LANGUAGE = 'ms'

TEST_PLAN_ID = 'test-plan'
TEST_PLAN_NAME = 'Test plan'

TEST_SUBMISSION_ID = 'my-test-submission'

TEST_FACEBOOK_APP_ID = 'fbappid123'

TEST_APP_ICON_IOS = {
    'name': 'index',
    'platform': 'ios',
    'height': 1024,
    'width': 1024,
    'image_format': 'png',
}

TEST_APP_ICON_ANDROID = {
    'name': 'index',
    'platform': 'android',
    'height': 512,
    'width': 512,
    'image_format': 'png',
}


def make_user():
    try:
        user = User.objects.get(username=TEST_USER_USERNAME)
    except User.DoesNotExist:
        user = User.objects.create_user(TEST_USER_USERNAME, TEST_USER_EMAIL)
        user.set_password(TEST_USER_PASSWORD)
        user.save()
    return user

def make_app(user):
    app = App.objects.create(
        user=user,
        name=TEST_APP_NAME,
        app_id=TEST_APP_ID,
        display_name=TEST_APP_DISPLAY_NAME,
        base_version=BaseVersion.objects.get(name=TEST_APP_BASE_VERSION),
        app_store_name = TEST_APP_DISPLAY_NAME,
        play_store_name = TEST_APP_DISPLAY_NAME,
        app_store_language = TEST_APP_LANGUAGE,
        play_store_language = TEST_APP_LANGUAGE,
    )
    # Assoiciate valid icons with the app
    ios_icon = AppIcon(name='index', height=1024, width=1024, platform='ios',
                image_format='png', app=app)
    android_icon = AppIcon(name='index', height=512, width=512,
                platform='android', image_format='png', app=app)
    ios_icon.save()
    android_icon.save()
    return app

def with_submission(func):
    @with_new_subscribed_user
    @with_new_app
    def wrapper(*args, **kwargs):
        user = make_user()
        app = App.objects.get(app_id=TEST_APP_ID)
        Submission.objects.create(
            submission_id=TEST_SUBMISSION_ID,
            app=app,
            user=user,
            base_version=app.base_version,
            display_name=app.display_name,
            status='processing',
            platform='ios',
            is_active=True
        )
        func(*args, **kwargs)
    return wrapper

def with_new_subscribed_user(func):
    def wrapper(*args, **kwargs):
        user = make_user()
        plan = Plan.objects.create(
            name=TEST_PLAN_NAME,
            plan_id=TEST_PLAN_ID,
            interval='monthly',
            seats=1,
            monthly_active_users=1000,
            max_app_size=512,
            priority_support=False,
            team_sharing=True,
            beta_tester_sharing=True
        )
        Subscription.objects.create(
            user=user,
            plan=plan,
            active=True,
            cancelled=False,
            chargebee_id='test-chargebee-id'
        )
        func(*args, **kwargs)
    return wrapper

# Decorator that creates a new user before running
def with_new_user(func):
    def wrapper(*args, **kwargs):
        make_user()
        func(*args, **kwargs)
    return wrapper

# Decorator that creates a new app before running
def with_new_app(func):
    def wrapper(*args, **kwargs):
        # We need at least one bundler and one streamer configured, because
        # it will be assigned to the new app
        Bundler(hostname='my.test.bundler').save()
        Streamer(hostname='my.test.streamer').save()
        BaseVersion(name=TEST_APP_BASE_VERSION, latest=True,
                      react_native_version=TEST_APP_REACT_NATIVE_VERSION).save()
        # Do the app dance
        user = make_user()
        make_app(user)
        func(*args, **kwargs)
    return wrapper
