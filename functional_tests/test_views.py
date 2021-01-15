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
from feed.models import Entry
User = get_user_model()
class BaseLiveServerTestCase(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Safari()
        self.wait = WebDriverWait(self.browser, MAX_WAIT)
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        cookie = self.client.cookies['sessionid']
        # NEED TO SETUP COOKIE
        self.browser.get(self.live_server_url)  #selenium will set cookie domain based on current page domain
        self.browser.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.browser.refresh() #need to update page for logged in user
        self.browser.get(self.live_server_url)
    
    def tearDown(self):
        self.browser.quit()
class FixturesTestCase(LiveServerTestCase):
    fixtures = ["data.json"]

    def setUp(self):
        self.browser = webdriver.Safari()
        self.wait = WebDriverWait(self.browser, MAX_WAIT)
        user = User.objects.first()
        self.client.force_login(user)
        cookie = self.client.cookies['sessionid']
        # NEED TO SETUP COOKIE
        self.browser.get(self.live_server_url)  #selenium will set cookie domain based on current page domain
        self.browser.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.browser.refresh() #need to update page for logged in user
        self.browser.get(self.live_server_url)
    def tearDown(self):
        self.browser.quit()
        
# TODO: Replace time.sleeps with waits
MAX_WAIT = 10
test_url = "https://www.example.org/feed.xml"
test_url_base = "https://www.example.org"
recent_date = datetime.datetime.now()
old_date = recent_date -  datetime.timedelta(days = 14)
test_page = f"""<feed xmlns="http://www.w3.org/2005/Atom"><generator uri="https://jekyllrb.com/" version="3.8.5">Jekyll</generator><link href="https://www.example.org/feed.xml" rel="self" type="application/atom+xml"/><link href="https://www.example.org/" rel="alternate" type="text/html"/><updated>2020-06-29T16:00:05+00:00</updated><id>https://www.example.org/feed.xml</id><title type="html">Example Feed</title><author><name>Example Writer</name></author><entry><title type="html">Entry 1</title><link href="https://www.example.org/1" rel="alternate" type="text/html" title="Entry 1"/><published>{recent_date}</published><updated>{recent_date}</updated><id>https://www.example.org/1</id><content type="html" xml:base="https://www.example.org/1">hello 1</content><author><name>Example Writer</name></author><summary type="html"/></entry><entry><title type="html">Entry 2</title><link href="https://www.example.org/2" rel="alternate" type="text/html" title="Entry 2"/><published>{old_date}</published><updated>{old_date}</updated><id>https://www.example.org/2</id><content type="html" xml:base="https://www.example.org/2">hello 2</content><author><name>Example Writer</name></author><summary type="html">hello 2</summary></entry></feed>"""
test_feed = feedparser.parse(test_page)
entries = ["Entry 1", "Entry 2"]
test_feed.etag = None
def fake_find_out_type(url):
    return (test_url, test_page , test_url)
def fake_feed_parser(a, *args, **kwargs):
    return test_feed

@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class FunctionalTest(BaseLiveServerTestCase):
    
    def test_inital(self, func_1, func_2):
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url)
        # They will see the form to add a new subscription and enter their url
        feed_form = self.browser.find_element_by_css_selector("#new_url_to_add")
        feed_form.send_keys(test_url)
        feed_form.send_keys(Keys.ENTER)
        # They will then see their URL appear in the subscriptions
        subscriptions = [sub.text for sub in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".subscription")))]
        self.assertEqual(len(subscriptions), 1)
        self.assertIn(test_url_base, subscriptions[0])
        # They will see all the entries they expected as well
        titles = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertEqual(entries, titles)
        # The user is happy, but they want to catch up on the past seven days. So they go to the latest page.
        self.browser.get(self.live_server_url + "/latest")
        # They see all the entries they expect there
        titles = [entry.text for entry in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__title"))) ]
        self.assertEqual(len(titles), 1)
        self.assertEqual([entries[0]], titles)

@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class CurrentlyReadingPageTest(FixturesTestCase):
    
    def test_can_set_things_to_currently_reading_and_not_currently_reading_on_home_page(self, func_1, func_2):
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url)
        # The user will mark an item as currently reading
        entry_1_title = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")][0]
        entry_1_currently_reading_button = self.browser.find_elements_by_class_name("entry__currently_reading__btn")[0]
        entry_1_currently_reading_button.click()
    
        # That item will disappear from the page
        entries_titles = [entry.text for entry in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__title"))) ]
        self.assertNotIn(entry_1_title, entries_titles)
        # The user will then go to the current page and see their item
        self.browser.get(self.live_server_url + "/current")
        entry_1_title = [entry.text for entry in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__title")))][0]
        entries_titles_from_current_page = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertIn(entry_1_title, entries_titles_from_current_page)
        # The user then decides they want to remove the item from their currently reading list
        entry_1_currently_reading_button = self.browser.find_elements_by_class_name("entry__currently_reading__btn")[0]
        entry_1_currently_reading_button.click()
        # The user no longer sees the item there
        entries_titles = self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".entry__title")))
            # There will only be 1, so once it's invisible it's all gone so it'll be True
        self.assertEqual(True, entries_titles)
        # The user visits the homepage and sees it
        self.browser.get(self.live_server_url)
        entries_titles = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertIn(entry_1_title, entries_titles)

    def test_can_set_things_to_currently_reading_and_not_currently_reading_on_latest_page(self, func_1, func_2):
        # ENSURE THEY ARE ALWAYS LATEST
        entry = Entry.objects.first()
        entry.published = datetime.datetime.now()
        entry.save()
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url)
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url+'/latest/')
        self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".main-title"), "Latest"))
        # The user will mark an item as currently reading
        entry_1_title = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".entry__title")))
        entry_1_title = entry_1_title.text
        entry_1_currently_reading_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".entry__currently_reading__btn")))
        entry_1_currently_reading_button.click()
    
        # That item will disappear from the page
        is_entry_gone = self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".entry__title")))
        self.assertEqual(is_entry_gone, True)
        # The user will then go to the current page and see their item
        self.browser.get(self.live_server_url + "/current")
        entry_1_title = [entry.text for entry in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__title"))) ][0]
        entries_titles_from_current_page = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertIn(entry_1_title, entries_titles_from_current_page)
        # The user then decides they want to remove the item from their currently reading list
        entry_1_currently_reading_button = self.browser.find_elements_by_class_name("entry__currently_reading__btn")[0]
        entry_1_currently_reading_button.click()
        # The user no longer sees the item there
        entries_titles = self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".entry__title"))) 
            # if True then it's invisible
        self.assertEqual(True, entries_titles)
        # The user visits the current page and sees it
        self.browser.get(self.live_server_url +'/latest')
        entries_titles = [entry.text for entry in self.browser.find_elements_by_class_name("entry__title")]
        self.assertIn(entry_1_title, entries_titles)
    def test_can_mark_items_as_read_and_unread(self, func_1, func_2):
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url)
        # The user will mark an item as unread
        entry_1_mark_reading_btn = self.browser.find_elements_by_class_name("entry__seen-unseen__btn")[0]
        entry_1_mark_reading_btn.click()
        # That item will be seen as read on the page
        entry_1_mark_reading_btn = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__seen-unseen__btn")))[0]
        self.assertNotIn("entry__seen-unseen__btn--unread", entry_1_mark_reading_btn.get_attribute("class"))
        entry_1_mark_reading_btn.click()
        # That user decides to remark it as unread on the page
        entry_1_mark_reading_btn = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".entry__seen-unseen__btn")))[0]
        self.assertIn("entry__seen-unseen__btn--unread", entry_1_mark_reading_btn.get_attribute("class"))

    def test_can_delete_subscription(self, func_1, func_2):
        # The user will open the web page to the homepage
        self.browser.get(self.live_server_url)
        # They will then see their one subscription
        subscriptions = [sub.text for sub in self.browser.find_elements_by_class_name("subscription")]
        self.assertEqual(len(subscriptions), 1)
        # They will delete their subscription
        subscription_delete_btn = self.browser.find_element_by_class_name("subscription__delete")
        subscription_delete_btn.click()
        # The subscription will be gone
        self.assertEqual(True, self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".subscription"))))
        # The entries also will be gone, as there was just one subscription
        self.assertEqual([], self.browser.find_elements_by_class_name("entry__title"))