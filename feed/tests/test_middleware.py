from django.test import TestCase
from unittest import mock
from django.contrib.auth import get_user_model
User = get_user_model()
class BaseTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
fake_urls_from_get = ['https://example.org/SUPERFAKEURL', "https://example.org/anotherFakeURL"]
def mocked_get_urls(url_that_you_want_urls_from):
    return fake_urls_from_get

@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
class MiddlewareRedirectsWhenItHasContext(BaseTestCase):
    # if the confirmation page has not been completed, then it should redirect 
    # this will require custom middleware
    def test_redirect_if_confirmation_flow_was_interrupted_and_session_data_still_there(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'}, follow=True)
        session = self.client.session
        self.assertEqual(session["temp_urls"], fake_urls_from_get)
        try_to_get_homepage = self.client.get('/')
        self.assertRedirects(try_to_get_homepage, '/feed/utils/find_urls_on_page/confirmation')

