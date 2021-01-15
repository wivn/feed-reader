from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unittest import mock
import feedparser
import time
import datetime
from django.core.management import call_command
from django.contrib.auth import get_user_model
User = get_user_model()

MAX_WAIT = 10
test_url = "https://www.example.org/feed.xml"
test_url_base = "https://www.example.org"
recent_date = datetime.datetime.now()
old_date = recent_date - datetime.timedelta(days=14)
test_page = f"""<feed xmlns="http://www.w3.org/2005/Atom"><generator uri="https://jekyllrb.com/" version="3.8.5">Jekyll</generator><link href="https://www.example.org/feed.xml" rel="self" type="application/atom+xml"/><link href="https://www.example.org/" rel="alternate" type="text/html"/><updated>2020-06-29T16:00:05+00:00</updated><id>https://www.example.org/feed.xml</id><title type="html">Example Feed</title><author><name>Example Writer</name></author><entry><title type="html">Entry 1</title><link href="https://www.example.org/1" rel="alternate" type="text/html" title="Entry 1"/><published>{recent_date}</published><updated>{recent_date}</updated><id>https://www.example.org/1</id><content type="html" xml:base="https://www.example.org/1">hello 1</content><author><name>Example Writer</name></author><summary type="html"/></entry><entry><title type="html">Entry 2</title><link href="https://www.example.org/2" rel="alternate" type="text/html" title="Entry 2"/><published>{old_date}</published><updated>{old_date}</updated><id>https://www.example.org/2</id><content type="html" xml:base="https://www.example.org/2">hello 2</content><author><name>Example Writer</name></author><summary type="html">hello 2</summary></entry></feed>"""
test_feed = feedparser.parse(test_page)
entries = ["Entry 1", "Entry 2"]
test_feed.etag = None


def fake_find_out_type(url):
    return (test_url, test_page, test_url)


def fake_feed_parser(a, *args, **kwargs):
    return test_feed

fake_urls_from_get = ['https://example.org/SUPERFAKEURL', "https://example.org/anotherFakeURL"]
def mocked_get_urls(url_that_you_want_urls_from):
    return fake_urls_from_get

@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class FunctionalTest(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Safari()
        self.wait = WebDriverWait(self.browser, MAX_WAIT)

    def tearDown(self):
        self.browser.quit()

    def test_inital(self, func_1, func_2):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        user_2 = User.objects.create_user(username="secondself", password="superCoolPassword")
        user_2.save()
        # The user will login and see that they are authenticated
        self.browser.get(self.live_server_url + '/registration/login')
        username_input = self.browser.find_element_by_id("id_username")
        username_input.send_keys("myself")
        password_input = self.browser.find_element_by_id("id_password")
        password_input.send_keys("superCoolPassword")
        password_input.send_keys(Keys.ENTER)
        # They will wait until they see the title
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Main"))
        # They will notice the page has no subscriptions or entry interactions
        empty_subs_element = self.browser.find_element_by_class_name("subs")
        self.assertEqual(len(empty_subs_element.find_elements_by_css_selector("*")), 0)
        empty_entries_element = self.browser.find_element_by_class_name("all-entries")
        self.assertEqual(len(empty_entries_element.find_elements_by_css_selector("*")), 0)
        # The user adds a subscription
        feed_form = self.browser.find_element_by_css_selector("#new_url_to_add")
        feed_form.send_keys(test_url)
        feed_form.send_keys(Keys.ENTER)
        # The user logs out after seeing the subscription and entries successfuly added
        subscriptions = [sub.text for sub in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".subscription")))]
        self.assertEqual(len(subscriptions), 1)
        self.assertIn(test_url_base, subscriptions[0])
        titles = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertEqual(entries, titles)
        self.browser.find_element_by_id("nav__logout").click()
        # The second user goes to the computer and clicks the relogin button
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#logout-relogin"))).click()
        # The second user logs in 
        username_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#id_username")))
        username_input.send_keys("secondself")
        password_input = self.browser.find_element_by_id("id_password")
        password_input.send_keys("superCoolPassword")
        password_input.send_keys(Keys.ENTER)
        # The second user does not see the subscription that was added nor the new entry interaction
        second_user_empty_subs = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".subs")))
        self.assertEqual(len(second_user_empty_subs.find_elements_by_css_selector(".subscription")), 0)
        second_user_empty_entries = self.browser.find_element_by_class_name("all-entries")
        time.sleep(5.0)
        self.assertEqual(len(second_user_empty_entries.find_elements_by_css_selector(".entry")), 0)

    @mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
    def test_adding_external_urls_does_not_interfere_with_more_users(self, func_1, func_2, func_3):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        user_2 = User.objects.create_user(username="secondself", password="superCoolPassword")
        user_2.save()
        # User #1 logs in and adds a URL
        self.browser.get(self.live_server_url + '/registration/login')
        username_input = self.browser.find_element_by_id("id_username")
        username_input.send_keys("myself")
        password_input = self.browser.find_element_by_id("id_password")
        password_input.send_keys("superCoolPassword")
        password_input.send_keys(Keys.ENTER)
        # The user then sees the main page and goes to the current page
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Main"))
        self.browser.get(self.live_server_url + '/current')
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Current"))
        # They then enter their URL and see the result
        form = self.wait.until(EC.visibility_of_element_located((By.NAME, 'urls_from_page')))
        form.send_keys("https://example.org")
        form.send_keys(Keys.ENTER)
        possible_urls = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".url_confirmation__possiblities")))
        possible_urls = [url.text for url in possible_urls]
        self.assertEqual(fake_urls_from_get, possible_urls)
        # Then they log out
        self.browser.find_element_by_id("nav__logout").click()
        # The second user goes to the computer and clicks the relogin button
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#logout-relogin"))).click()
        # The second user logs in 
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#id_username")))
        username_input = self.browser.find_element_by_id("id_username")
        username_input.send_keys("secondself")
        password_input = self.browser.find_element_by_id("id_password")
        password_input.send_keys("superCoolPassword")
        password_input.send_keys(Keys.ENTER)
        # They ARE NOT redirected to the confirm URLs page because they have no URLs to confirm
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Main"))
        # They then go to the current page
        self.browser.get(self.live_server_url + "/current")
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Current"))
        # The user will then find the form and enter in their url
        form = self.browser.find_element_by_name('urls_from_page')
        form.send_keys("https://example.org")
        form.send_keys(Keys.ENTER)
        # User #2 adds a URL and none of the links from User #1 on the confirmation page show up (which means only two will show up as per normal)
        self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".url_confirmation__possiblities")))
        possible_urls = [url for url in possible_urls]
        self.assertEqual(fake_urls_from_get, possible_urls)
        self.browser.find_element_by_id('url_confirmation__accept').click()
        # They will see only their URLs appear
        posts = [url.text for url in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".feedless_post")))]
        self.assertEqual(fake_urls_from_get, posts)
