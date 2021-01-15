from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unittest import mock 
import time
from django.contrib.auth import get_user_model
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
MAX_WAIT = 5
fake_urls_from_get = ['https://example.org/SUPERFAKEURL', "https://example.org/anotherFakeURL"]
def mocked_get_urls(url_that_you_want_urls_from):
    return fake_urls_from_get
class element_has_single_css_selector(object):
  """An expectation for checking that an element has a particular css class.

  locator - used to find the element
  returns the WebElement once it has the particular css class
  """
  def __init__(self, css_selector):
    self.css_selector = css_selector

  def __call__(self, driver):
    elements = driver.find_elements_by_css_selector(self.css_selector)
    if len(elements) == 1:
        return elements
    else:
        return False

# I enabled Safari https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
class FunctionalTest(BaseLiveServerTestCase):


	@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
	def test_inital(self, mocked_func):
		user_url = "example.com/superFakeURLThanks"
		# The user will open the web page TO THE CURRENT PAGE and is excited and ready to add all
		self.browser.get(self.live_server_url + '/current/') # currently_reading url/view
		# The user will then find the form and enter in their url
		form = self.wait.until(EC.visibility_of_element_located((By.NAME, 'urls_from_page')))
		form.send_keys(user_url)
		form.send_keys(Keys.ENTER)
		# The user will get a confirmation box, confirming the URLs they'd like to add
		# They will see the URLs they are expecting and click the accept button
		possible_urls = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".url_confirmation__possiblities")))
		possible_urls = [url.text for url in possible_urls]
		self.assertEqual(fake_urls_from_get, possible_urls)
		self.browser.find_element_by_id('url_confirmation__accept').click()
		# The user will then see the urls they expect to appear, 
		# appear in their feed in their right place
		posts = [url.text for url in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".feedless_post")))]
		self.assertEqual(fake_urls_from_get, posts)

	@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
	def test_can_delete_options_from_url_possibilities(self, mocked_func):
		user_url = "example.com/superFakeURLThanks"
		# The user will open the web page TO THE CURRENT PAGE and is excited and ready to add all
		self.browser.get(self.live_server_url + '/current/') # currently_reading url/view
		# The user will then find the form and enter in their url
		form = self.browser.find_element_by_name('urls_from_page')
		form.send_keys(user_url)
		form.send_keys(Keys.ENTER)
		# The user will get a confirmation box, confirming the URLs she'd like to add
		# They will see the URLs they're expecting and click the accept button
		possible_urls = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".url_confirmation__possiblities")))
		possible_urls = [url.text for url in possible_urls]
		self.assertEqual(fake_urls_from_get, possible_urls)
		# They will then delete one of the URLs as she doesn't want it
		deletion_buttons = self.browser.find_elements_by_css_selector(".url_confirmation__delete")
		self.assertNotEqual(deletion_buttons, [])
		# They will then delete the first one
		deletion_buttons[0].click()
		# They then see that the second URL is no longer there
		new_possible_urls = [url.text for url in self.wait.until(element_has_single_css_selector(".url_confirmation__possiblities"))]
		self.assertNotEqual(fake_urls_from_get, new_possible_urls)
		self.assertEqual(len(new_possible_urls), 1)
		self.assertEqual([fake_urls_from_get[1]], new_possible_urls)
		self.browser.find_element_by_id('url_confirmation__accept').click()
		# The user will then see the urls they expect to appear, 
		# appear in their feed in their right place
		posts = [url.text for url in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".feedless_post"))) ]
		# Since the first URL was deleted, we will only expect the second
		self.assertEqual([fake_urls_from_get[1]], posts)

	def test_can_enter_fake_url_and_get_an_error_message(self):
		user_url = "example"
		# The user will open the web page TO THE CURRENT PAGE and is excited and ready to add all
		self.browser.get(self.live_server_url + '/current/') # currently_reading url/view
		# The user will then find the form and enter in their url
		form = self.browser.find_element_by_name('urls_from_page')
		form.send_keys(user_url)
		form.send_keys(Keys.ENTER)
		# The user entered in a URl that does not work and recieves an appropriate error message
		err_msg = [msg.text for msg in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".possible_message")))]
		self.assertEqual(err_msg[0], "There was a problem processing that URL. Please enter a valid URL and try again later.")

	@mock.patch('feed.views.urlsOnPage', side_effect=mocked_get_urls)
	def test_can_delete_feedless_urls(self, func_1):
		user_url = "example.com/superFakeURLThanks"
		# The user will open the web page TO THE CURRENT PAGE and is excited and ready to add all
		self.browser.get(self.live_server_url + '/current/') # currently_reading url/view
		# The user will then find the form and enter in their url
		form = self.browser.find_element_by_name('urls_from_page')
		form.send_keys(user_url)
		form.send_keys(Keys.ENTER)
		# The user will get a confirmation box, confirming the URLs she'd like to add
		# They will see the URLs they're expecting and click the accept button
		possible_urls = self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".url_confirmation__possiblities")))
		possible_urls = [url.text for url in possible_urls]
		self.assertEqual(fake_urls_from_get, possible_urls)
		# They will then accept the urls they are accepting
		self.browser.find_element_by_id('url_confirmation__accept').click()
		# They will then see the urls they expect to appear, 
		initial_entries = [url.text for url in self.wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".feedless_post"))) ]
		# They will then delete the first feedless entry
		self.browser.find_elements_by_class_name("feedless_post--delete")[0].click()
		# They will then only see one URL there
		entries = [url.text for url in self.wait.until(element_has_single_css_selector(".feedless_post")) ]
		self.assertNotEqual(initial_entries,entries)
		self.assertEqual(len(entries), 1)
		self.assertEqual(entries[0], fake_urls_from_get[1])