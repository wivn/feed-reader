# The user tries to access the homepage, then the latest page and finally the current page
#  but they are redirected to the login/signup page each time
from django.test import TestCase
from django.shortcuts import redirect, reverse
from django.contrib.auth import get_user_model
from ..models import EntryInteraction, FeedlessEntry, Subscription, Entry
from unittest import mock
import datetime
import feedparser

User = get_user_model()

class CorrectRedirectsDueToAuth(TestCase):
    def test_homepage_redirects_when_not_authenticated(self):
        response = self.client.get(reverse('feed:index'))
        # remove last slash from first reverse so the URL matches correctly
        self.assertRedirects(response, f'{reverse("registration:login")[:-1]}?next={reverse("feed:index")}', status_code=302, target_status_code=301)
    def test_homepage_DOES_NOT_redirect_when_authenticated(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('feed:index'))
        self.assertEqual(response.status_code, 200)

    def test_latest_redirects_when_not_authenticated(self):
        response = self.client.get(reverse('feed:latest'))
        # remove last slash from first reverse so the URL matches correctly
        self.assertRedirects(response, f'{reverse("registration:login")[:-1]}?next={reverse("feed:latest")}', status_code=302, target_status_code=301)
    def test_latest_DOES_NOT_redirect_when_authenticated(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('feed:latest'))
        self.assertEqual(response.status_code, 200)

    def test_current_page_redirects_when_not_authenticated(self):
        response = self.client.get(reverse('feed:currently_reading'))
        # remove last slash from first reverse so the URL matches correctly
        self.assertRedirects(response, f'{reverse("registration:login")[:-1]}?next={reverse("feed:currently_reading")}', status_code=302, target_status_code=301)
    def test_current_page_DOES_NOT_redirect_when_authenticated(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('feed:currently_reading'))
        self.assertEqual(response.status_code, 200)

class CannotEditOtherUsersData(TestCase):
    fixtures = ["data.json"]

    def setUp(self):
        
        feedless_entry = FeedlessEntry(url="https://example.org", user=User.objects.first())
        feedless_entry.save()

        # A user already exists, create a second user and try to modify the first users things
        user = User.objects.create_user(username="second_user", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
    def test_cannot_modify_other_users_EntryInteraction(self):
        entry_interaction = EntryInteraction.objects.first()
        self.assertEqual(entry_interaction.read, False)
        self.assertEqual(entry_interaction.currently_reading, False)
        
        self.client.post(reverse('feed:mark_as_currently_reading', args=[entry_interaction.pk]))
        self.client.post(reverse('feed:change_entry_read_status', args=[entry_interaction.pk]))
        # there should be no change
        entry_interaction = EntryInteraction.objects.first()
        self.assertEqual(entry_interaction.read, False)
        self.assertEqual(entry_interaction.currently_reading, False)

    def test_cannot_delete_other_users_feedlessentry(self):
        entry = FeedlessEntry.objects.first()
        self.assertEqual(entry.url, "https://example.org")
        
        self.client.post(reverse('feed:feedless_entry_deletion', args=[entry.pk]))
        # there should be no change
        entry = FeedlessEntry.objects.first()
        self.assertEqual(entry.url, "https://example.org")

test_url = "https://www.example.org/feed.xml"
test_url_base = "https://www.example.org/"
recent_date = datetime.datetime.now()
old_date = recent_date -  datetime.timedelta(days = 14)
test_page = f"""<feed xmlns="http://www.w3.org/2005/Atom"><generator uri="https://jekyllrb.com/" version="3.8.5">Jekyll</generator><link href="https://www.example.org/feed.xml" rel="self" type="application/atom+xml"/><link href="https://www.example.org/" rel="alternate" type="text/html"/><updated>2020-06-29T16:00:05+00:00</updated><id>https://www.example.org/feed.xml</id><title type="html">Example Feed</title><author><name>Example Writer</name></author><entry><title type="html">Entry 1</title><link href="https://www.example.org/1" rel="alternate" type="text/html" title="Entry 1"/><published>{recent_date}</published><updated>{recent_date}</updated><id>https://www.example.org/1</id><content type="html" xml:base="https://www.example.org/1">hello 1</content><author><name>Example Writer</name></author><summary type="html"/></entry><entry><title type="html">Entry 2</title><link href="https://www.example.org/2" rel="alternate" type="text/html" title="Entry 2"/><published>{old_date}</published><updated>{old_date}</updated><id>https://www.example.org/2</id><content type="html" xml:base="https://www.example.org/2">hello 2</content><author><name>Example Writer</name></author><summary type="html">hello 2</summary></entry></feed>"""
test_feed = feedparser.parse(test_page)
test_entry_1 = test_feed.entries[0]
test_entry_2 = test_feed.entries[1]
entries = ["Entry 1", "Entry 2"]
test_feed.etag = None
def fake_find_out_type(url):
    return (test_url, test_page , test_url)
def fake_feed_parser(a, *args, **kwargs):
    return test_feed

@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class CannotAddNewSubscription(TestCase):
    def setUp(self):   
        first_user = User.objects.create_user(username="first_user", password="superCoolPassword")
        first_user.save()
        self.first_user = first_user
        # A user already exists, create a second user and try to modify the first users things
        user = User.objects.create_user(username="second_user", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        self.main_user = user

    def test_cannot_add_subscription_to_other_user(self, func_1, func_2):
        self.assertEqual(len(Subscription.objects.filter(user=self.first_user)), 0)
        self.assertEqual(len(Subscription.objects.filter(user=self.main_user)), 0)
        response = self.client.post(reverse('feed:add_feed'),  data={'url': 'example.org', 'page_type': 'index'})
        self.assertEqual(len(Subscription.objects.all()), 1)
        self.assertEqual(len(Subscription.objects.filter(user=self.first_user)), 0)
        self.assertEqual(len(Subscription.objects.filter(user=self.main_user)), 1)
    

class CannotDeleteNorReloadNonOwnedSubs(TestCase):
    fixtures = ["data.json"]
    def setUp(self):   
        self.first_user = User.objects.first()
        # A user already exists, create a second user and try to modify the first users things
        user = User.objects.create_user(username="second_user", password="superCoolPassword")
        user.save()
        self.client.force_login(user)
        self.main_user = user
    def test_cannot_add_subscription_to_other_user(self):
        pk = Subscription.objects.first().pk
        self.assertEqual(len(Subscription.objects.all()), 1)
        response = self.client.post(reverse('feed:delete_subscription'),  data={'id': pk})
        # Object still exists
        self.assertEqual(len(Subscription.objects.all()), 1)
    
    # DANGER: IF THIS TEST FAILS IT WILL BE GETTING A URL FROM AN EXTERNAL SITE, EACH TIME IT RUNS IN FAILURE IT WILL REQUEST THE EXTERNAL SITE
    def test_does_not_reload_subscriptions_of_other_user(self):
        self.assertEqual(len(Entry.objects.all()), 20)
        response = self.client.post(reverse('feed:reload_all_feeds'))
        self.assertEqual(len(Entry.objects.all()), 20)