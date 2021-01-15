from django.shortcuts import redirect, reverse
from django.test import TestCase
from ..models import FeedlessEntry
from unittest import mock
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
User = get_user_model()

# Adds URLS from URL
fake_urls_from_get = ['https://example.org/SUPERFAKEURL', "https://example.org/anotherFakeURL"]
def mocked_get_urls(url_that_you_want_urls_from):
    return fake_urls_from_get

class BaseTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        self.user = user

@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
class ConfirmationPage(BaseTestCase):
    def test_post_redirects_to_confirmation_page(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        self.assertRedirects(response, '/feed/utils/find_urls_on_page/confirmation')
    def test_context_contains_expected_items_on_confirmation_page(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'}, follow=True)
        self.assertEquals(response.context['possible_urls'], fake_urls_from_get)

    def test_displays_expected_items_on_confirmation_page(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'}, follow=True)
        self.assertContains(response, fake_urls_from_get[0])
        self.assertContains(response, fake_urls_from_get[1])
       
        self.assertContains(response, "Add URLs") # add urls button text
    
    def test_renders_correct_template(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feed/urls_on_page_confirmation.html')
    

@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
class ConfirmationAcceptingDeletionIntegrationTest(BaseTestCase):
    def test_can_delete_urls_from_page(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()

        response = self.client.post(reverse('feed:delete_from_temp_urls_session'), data={'url_to_delete_index': 0}, follow=True)
        self.assertNotIn( fake_urls_from_get[0], response.content.decode())
        self.assertIn(fake_urls_from_get[1], response.content.decode(), )
    def test_can_deleted_urls_are_not_show_on_final_page(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()

        self.client.post(reverse('feed:delete_from_temp_urls_session'), data={'url_to_delete_index': 0}, follow=True)
        
        response = self.client.post(reverse('feed:save_urls_from_page_confirm_urls'),follow=True)
        self.assertNotIn(fake_urls_from_get[0], response.content.decode())
        self.assertIn(fake_urls_from_get[1], response.content.decode(), )
    
    def test_delete_redirects_to_the_correct_page(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()

        response = self.client.post(reverse('feed:delete_from_temp_urls_session'), data={'url_to_delete_index': 0}, follow=True)
        self.assertRedirects(response, reverse('feed:save_urls_from_page_confirmation'))
    
    def test_empty_POST_requests_still_redirect(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()

        response = self.client.post(reverse('feed:delete_from_temp_urls_session'))
        self.assertRedirects(response, reverse('feed:save_urls_from_page_confirmation'))
    
    def test_empty_accidental_GET_requests_still_redirect(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()

        response = self.client.get(reverse('feed:delete_from_temp_urls_session'))
        self.assertRedirects(response, reverse('feed:save_urls_from_page_confirmation'))

@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
class CurrentPage(BaseTestCase):
    # adds Urls from page 
    def test_url_can_support_schemeless_urls(self, mock_get_urls_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        # After the URL is sent, one TempItem should be found
        session = self.client.session
        # After the urls are confirmed, a FeedlessEntry created and should up on the page
        response = self.client.post('/feed/utils/find_urls_on_page/confirm_urls', follow=True)
        feedless_entry = FeedlessEntry.objects.values_list('url', flat=True)
        self.assertEqual(list(feedless_entry), fake_urls_from_get)
    def test_url_feedless_entries_are_saved(self, mock_get_urls_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        # After the URL is sent, one TempItem should be found
        session = self.client.session
        # After the urls are confirmed, a FeedlessEntry created and should up on the page
        response = self.client.post('/feed/utils/find_urls_on_page/confirm_urls', follow=True)
        feedless_entry = FeedlessEntry.objects.values_list('url', flat=True)
        self.assertEqual(list(feedless_entry), fake_urls_from_get)
    def test_feedless_urls_passed_to_template(self, mock_get_urls_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        # After the URL is sent, one TempItem should be found
        session = self.client.session
        # After the urls are confirmed, a FeedlessEntry created and should up on the page
        response = self.client.post('/feed/utils/find_urls_on_page/confirm_urls', follow=True)
        for url in fake_urls_from_get:
            self.assertContains(response, url)
    
    def test_correct_template_used(self, mock_get_urls_func):
        response = self.client.post(reverse('feed:save_urls_from_page_confirm_urls'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feed/currently_reading.html')
@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
class AcceptingConfirmationPage(BaseTestCase):
    
    def test_temp_items_are_passed_to_session(self, mock_get_urls_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        # After the URL is sent, temp items should be found
        session = self.client.session
        self.assertEqual(session["temp_urls"], fake_urls_from_get)
   
    def test_temp_items_cleared_on_acceptance(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()
        # After the urls are confirmed, the session data should be cleared
        response = self.client.post(reverse('feed:save_urls_from_page_confirm_urls'))
        self.assertEqual(self.client.session.get("temp_urls", None), None)

    def test_POST_request_redirects_to_current_with_session_data(self, mock_get_urls_func):
        session = self.client.session
        session["temp_urls"] = fake_urls_from_get
        session.save()
        
        # this test will not work if session data isn't cleared
        response = self.client.post(reverse('feed:save_urls_from_page_confirm_urls'),)
        # confirm_urls should redirect to the current page
        self.assertRedirects(response, '/current/')
    
    def test_POST_request_redirects_to_current_without_session_data(self, mock_get_urls_func):
        # this test will not work if session data isn't cleared
        response = self.client.post(reverse('feed:save_urls_from_page_confirm_urls'),)
        # confirm_urls should redirect to the current page
        self.assertRedirects(response, '/current/')
class ConfirmationPageIntegrationWithRealSite(BaseTestCase):
    @mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
    def test_url_can_support_schemeless_urls(self, mocked_get_urls_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.org'})
        session = self.client.session
        self.assertEqual(session["temp_urls"],  fake_urls_from_get)
    @mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
    def test_url_can_support_www_schemless_urls(self, mock_get_urls_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'www.example.org'})
        session = self.client.session
        self.assertEqual(session["temp_urls"],  fake_urls_from_get)
    
    def test_rejects_things_with_the_wrong_scheme(self):
        response = self.client.post(reverse('feed:save_urls_from_page'), data={'urls_from_page': 'mail://example.org'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'There was a problem processing that URL. Please enter a valid URL and try again later.')

        session = self.client.session
        self.assertEqual(session.get("temp_urls", None), None)
    
    def test_rejects_things_that_are_not_urls(self):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'There was a problem processing that URL. Please enter a valid URL and try again later.')
        
        session = self.client.session
        self.assertEqual(session.get("temp_urls", None), None)

    def test_fake_url_fails(self):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'example.test'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'There was a problem processing that URL. Please enter a valid URL and try again later.')
        
        session = self.client.session
        self.assertEqual(session.get("temp_urls", None), None)
    
    def test_redirects_correct_on_error(self):
        response = self.client.post(reverse('feed:save_urls_from_page'), data={'urls_from_page': 'example'})
        self.assertRedirects(response, reverse('feed:currently_reading'))

@mock.patch('feed.views.urlsOnPage', side_effect= lambda x: [])
class EmptyErrorMessage(BaseTestCase):

    def test_redirects_correct_on_error(self, fake_urls_from_get_func):
        response = self.client.post(reverse('feed:save_urls_from_page'), data={'urls_from_page': 'www.example.org'})
        self.assertRedirects(response, reverse('feed:currently_reading'))
    
    def test_does_not_save_anything_to_temp_urls(self, fake_urls_from_get_func):
        self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'www.example.org'})
        session = self.client.session
        self.assertEqual(session.get("temp_urls", None),  None)
    
    def test_returns_error_via_message_that_it_is_empty(self, fake_urls_from_get_func):
        response = self.client.post('/feed/utils/find_urls_on_page', data={'urls_from_page': 'www.example.org'})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'The webpage you submitted has no URLs on it.')

class CanInteractWithFeedlessEntries(BaseTestCase):
    
    def test_can_delete_feedless_entry_via_POST_request(self):
        feedless_entry = FeedlessEntry(url="https://www.example.org", user=self.user)
        feedless_entry.save()
        self.assertEqual(len(FeedlessEntry.objects.all()), 1)
        self.assertEqual(FeedlessEntry.objects.first(), feedless_entry)
        self.client.post(reverse("feed:feedless_entry_deletion",args=[feedless_entry.pk]))
        self.assertEqual(len(FeedlessEntry.objects.all()), 0)

    def test_can_delete_feedless_entry_from_page(self):
        feedless_entry = FeedlessEntry(url="https://www.example.org", user=self.user)
        feedless_entry.save()
        response_initial = self.client.get(reverse("feed:currently_reading"))
        self.assertIn(feedless_entry.url, response_initial.content.decode('ascii'))
        self.client.post(reverse("feed:feedless_entry_deletion",args=[feedless_entry.pk]))
        response_after_deletion = self.client.get(reverse("feed:currently_reading"))
        self.assertNotIn(feedless_entry.url, response_after_deletion.content.decode('ascii'))