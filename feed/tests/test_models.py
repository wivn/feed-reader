from django.test import TestCase
from ..models import FeedlessEntry
from django.contrib.auth import get_user_model
User = get_user_model()
class BaseTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        self.user = user
class FeedlessEntryTest(BaseTestCase):
    def test_url_showcases_as_string(self):
        FeedlessEntry.objects.create(url="https://example.org", user=self.user)
        entry = FeedlessEntry.objects.first()
        self.assertEqual(entry.url, "https://example.org")