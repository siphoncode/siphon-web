
from django.test import client, TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class TestAnalyticsSecurity(TestCase):
    def setUp(self):
        self.client = client.Client()

    def test_analytics__not_authenticated(self):
        response = self.client.get(reverse('analytics:analytics'))
        self.assertEqual(response.status_code, 404)

    def test_analytics__not_staff(self):
        # Make a non-staff user
        user = User.objects.create_user('myuser', 'a@b.com')
        user.set_password('mypass')
        user.save()
        self.assertFalse(user.is_staff)
        # Login, get page should fail
        self.client.login(username='myuser', password='mypass')
        response = self.client.get(reverse('analytics:analytics'))
        self.assertEqual(response.status_code, 404)

    def test_analytics__is_staff(self):
        # Make a staff user
        user = User.objects.create_user('staffuser', 'a@b.com')
        user.set_password('mypass')
        user.is_staff = True
        user.save()
        # Should be allowed
        self.client.login(username='staffuser', password='mypass')
        response = self.client.get(reverse('analytics:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Analytics' in str(response.content))
