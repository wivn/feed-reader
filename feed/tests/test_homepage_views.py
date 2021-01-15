from django.shortcuts import redirect, reverse
from django.test import TestCase
from ..models import Subscription, EntryInteraction, SiteFeed, Entry
from unittest import mock
import datetime
import feedparser
import os
from django.contrib.auth import get_user_model
User = get_user_model()
class BaseTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="myself", password="superCoolPassword")
        user.save()
        self.client.force_login(user)

class FixturesTestCase(TestCase):
    fixtures = ["data.json"]

    def setUp(self):
        user = User.objects.first()
        self.client.force_login(user)

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
class AddingNewURLs(BaseTestCase):
    def test_adding_new_url_redirects_to_a_homepage(self, func_1, func_2):
        response = self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        self.assertRedirects(response, reverse("feed:index"))
    def test_subscription_is_created(self, func_1, func_2):
        response = self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        sub = Subscription.objects.first()
        self.assertEqual(sub.feed.url, test_url_base)
        self.assertEqual(sub.last_updated, None)
    def test_entries_are_correctly_created(self, func_1, func_2):
        response = self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        entries = Entry.objects.all()
        entry_1 = entries[0]
        self.assertEqual(entry_1.title, test_entry_1.title)
        self.assertEqual(entry_1.url, test_entry_1.id)
        self.assertEqual(entry_1.content, test_entry_1.content[0].value)
        self.assertEqual(entry_1.summary, test_entry_1.summary)
        self.assertEqual(entry_1.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_1.published)
        self.assertEqual(entry_1.story_id, test_entry_1.id)
        self.assertEqual(entry_1.feed, SiteFeed.objects.first())
        entry_2 = entries[1]
        self.assertEqual(entry_2.title, test_entry_2.title)
        self.assertEqual(entry_2.url, test_entry_2.id)
        self.assertEqual(entry_2.content, test_entry_2.content[0].value)
        self.assertEqual(entry_2.summary, test_entry_2.summary)
        self.assertEqual(entry_2.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_2.published)
        self.assertEqual(entry_2.story_id, test_entry_2.id)
        self.assertEqual(entry_2.feed, SiteFeed.objects.first())
    def test_SiteFeed_is_created(self, func_1, func_2):
        response = self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.url, test_url_base)
        self.assertEqual(feed.feed_url, test_url)
        self.assertEqual(feed.title, "Example Feed")
        # checks that both are the same day, since the mock doesn't return a last_modified time, it uses the current time
        self.assertEqual(feed.last_modified.date(), recent_date.date())
        self.assertEqual(feed.etag, None)  

@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class HomepageTests(BaseTestCase):
    def test_entry_interactions_are_created_correctly_when_feed_is_added_and_homepage_is_loaded(self, func_1, func_2):
        self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        response = self.client.get(reverse("feed:index"))

        values_from_entries = EntryInteraction.objects.values('read', 'currently_reading', 'sub').all()
        self.assertEqual(values_from_entries[0], {'read': False, 'currently_reading': False, 'sub': 1})
        self.assertEqual(values_from_entries[1], {'read': False, 'currently_reading': False, 'sub': 1})

        entries = EntryInteraction.objects.all()
        entry_1 = entries[0].connection
        self.assertEqual(entry_1.title, test_entry_1.title)
        self.assertEqual(entry_1.url, test_entry_1.id)
        self.assertEqual(entry_1.content, test_entry_1.content[0].value)
        self.assertEqual(entry_1.summary, test_entry_1.summary)
        self.assertEqual(entry_1.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_1.published)
        self.assertEqual(entry_1.story_id, test_entry_1.id)
        self.assertEqual(entry_1.feed, SiteFeed.objects.first())
        entry_2 = entries[1].connection
        self.assertEqual(entry_2.title, test_entry_2.title)
        self.assertEqual(entry_2.url, test_entry_2.id)
        self.assertEqual(entry_2.content, test_entry_2.content[0].value)
        self.assertEqual(entry_2.summary, test_entry_2.summary)
        self.assertEqual(entry_2.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_2.published)
        self.assertEqual(entry_2.story_id, test_entry_2.id)
        self.assertEqual(entry_2.feed, SiteFeed.objects.first())
    def test_uses_correct_template(self, func_1, func_2):
        response = self.client.get(reverse("feed:index"))
        self.assertTemplateUsed(response, "feed/index.html")
@mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
class LatestPageTest(BaseTestCase):
    def test_entry_interactions_are_created_correctly_when_feed_is_added_and_latestpast_is_loaded(self, func_1, func_2):
        self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        response = self.client.get(reverse("feed:latest"))

        values_from_entries = EntryInteraction.objects.values('read', 'currently_reading', 'sub').all()
        self.assertEqual(values_from_entries[0], {'read': False, 'currently_reading': False, 'sub': 1})
        self.assertEqual(values_from_entries[1], {'read': False, 'currently_reading': False, 'sub': 1})

        entries = EntryInteraction.objects.all()
        entry_1 = entries[0].connection
        self.assertEqual(entry_1.title, test_entry_1.title)
        self.assertEqual(entry_1.url, test_entry_1.id)
        self.assertEqual(entry_1.content, test_entry_1.content[0].value)
        self.assertEqual(entry_1.summary, test_entry_1.summary)
        self.assertEqual(entry_1.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_1.published)
        self.assertEqual(entry_1.story_id, test_entry_1.id)
        self.assertEqual(entry_1.feed, SiteFeed.objects.first())
        entry_2 = entries[1].connection
        self.assertEqual(entry_2.title, test_entry_2.title)
        self.assertEqual(entry_2.url, test_entry_2.id)
        self.assertEqual(entry_2.content, test_entry_2.content[0].value)
        self.assertEqual(entry_2.summary, test_entry_2.summary)
        self.assertEqual(entry_2.published.strftime("%Y-%m-%d %H:%M:%S.%f"), test_entry_2.published)
        self.assertEqual(entry_2.story_id, test_entry_2.id)
        self.assertEqual(entry_2.feed, SiteFeed.objects.first())
    def test_uses_correct_template(self, func_1, func_2):
        response = self.client.get(reverse("feed:latest"))
        self.assertTemplateUsed(response, "feed/index.html")

class HomepageModifiesEntryProperties(FixturesTestCase):

    def test_can_mark_item_as_read_or_unread(self):
        pk = EntryInteraction.objects.first().pk
        self.assertEqual(EntryInteraction.objects.first().read, False)
        self.client.post(reverse('feed:change_entry_read_status', args=[pk]), data={'page_type': 'index'})
        self.assertEqual(EntryInteraction.objects.first().read, True)
        self.client.post(reverse('feed:change_entry_read_status', args=[pk]))
        self.assertEqual(EntryInteraction.objects.first().read, False)
    def test_can_mark_or_unmark_item_as_currently_reading(self):
        pk = EntryInteraction.objects.first().pk
        self.assertEqual(EntryInteraction.objects.first().currently_reading, False)
        self.client.post(reverse('feed:mark_as_currently_reading', args=[pk]), data={'page_type': 'index'})
        self.assertEqual(EntryInteraction.objects.first().currently_reading, True)
        self.client.post(reverse('feed:mark_as_currently_reading', args=[pk]))
        self.assertEqual(EntryInteraction.objects.first().currently_reading, False)

    def test_returns_index_page_when_changing_read_status(self):
        pk = EntryInteraction.objects.first().pk
        response = self.client.post(reverse('feed:change_entry_read_status', args=[pk]), data={'page_type': 'index'})
        self.assertRedirects(response, reverse('feed:index'))
    
    def test_returns_latest_page_when_changing_read_status(self):
        pk = EntryInteraction.objects.first().pk
        response = self.client.post(reverse('feed:change_entry_read_status', args=[pk]), data={'page_type': 'latest'})
        self.assertRedirects(response, reverse('feed:latest'))

    def test_returns_index_page_when_changing_currently_reading_status(self):
        pk = EntryInteraction.objects.first().pk
        response = self.client.post(reverse('feed:mark_as_currently_reading', args=[pk]), data={'page_type': 'index'})
        self.assertRedirects(response, reverse('feed:index'))
    
    def test_returns_latest_page_when_changing_currently_reading_status(self):
        pk = EntryInteraction.objects.first().pk
        response = self.client.post(reverse('feed:mark_as_currently_reading', args=[pk]), data={'page_type': 'latest'})
        self.assertRedirects(response, reverse('feed:latest'))

class ModifyingSubscriptionTests(FixturesTestCase):
    def test_can_delete_subscription(self):
        pk = Subscription.objects.first().pk
        self.assertEqual(len(Subscription.objects.all()), 1)
        self.client.post(reverse('feed:delete_subscription'), data={'page_type': 'index', 'id': pk})
        self.assertEqual(Subscription.objects.all().exists(), False)
    def test_sub_deletion_does_not_delete_SiteFeed(self):
        pk = Subscription.objects.first().pk
        site_feed = SiteFeed.objects.first()
        self.assertEqual(SiteFeed.objects.all()[0], site_feed)
        self.client.post(reverse('feed:delete_subscription'), data={'page_type': 'index', 'id': pk})
        self.assertEqual(SiteFeed.objects.all()[0], site_feed)

    def test_returns_index_page_on_redirect(self):
        pk = Subscription.objects.first().pk
        response = self.client.post(reverse('feed:delete_subscription'), data={'page_type': 'index', 'id': pk})
        self.assertRedirects(response, reverse('feed:index'))
    def test_returns_latest_page_on_redirect(self):
        pk = Subscription.objects.first().pk
        response = self.client.post(reverse('feed:delete_subscription'), data={'page_type': 'latest', 'id': pk})
        self.assertRedirects(response, reverse('feed:latest'))
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
updated_test_url = "http://feeds.feedburner.com/TechCrunch/startups"
file_data = open(os.path.join(__location__,'updated_feed.xml'),mode='r')
updated_test_page = file_data.read()
file_data.close()
updated_test_feed = feedparser.parse(updated_test_page)
def updated_fake_find_out_type(url):
    return (updated_test_url, updated_test_page, updated_test_url)
def updated_fake_feed_parser(a, *args, **kwargs):
    return updated_test_feed

@mock.patch('feed.feedTools.find_out_type', side_effect=updated_fake_find_out_type)
@mock.patch('feed.feedTools.feedparser.parse', side_effect=updated_fake_feed_parser)
class ReloadSubscription(FixturesTestCase):

    def test_reloading_subs_correct_redirect_for_index(self, func_1, func_2):
        response = self.client.post(reverse("feed:reload_all_feeds"), data={'page_type': 'index'})
        self.assertRedirects(response, reverse("feed:index"))
    def test_reloading_subs_correct_redirect_for_latest(self, func_1, func_2):
        response = self.client.post(reverse("feed:reload_all_feeds"), data={'page_type': 'latest'})
        self.assertRedirects(response, reverse("feed:latest"))
    def test_reloading_subs_results_in_new_entries(self, func_1, func_2):
        self.assertEqual(len(Entry.objects.all()), 20)
        self.assertEqual(Entry.objects.latest('published').title, "Point to launch new challenger bank with rewards on debit card purchases")
        self.client.post(reverse("feed:reload_all_feeds"), data={'page_type': 'index'})
        self.assertEqual(len(Entry.objects.all()), 40)
        self.assertEqual(Entry.objects.latest('published').title, "Extension rounds help some startups play offense during COVID-19")
    
    def test_reloading_subs_results_in_new_entry_interactions_and_updated_subscription(self, func_1, func_2):
        self.assertEqual(len(EntryInteraction.objects.all()), 20)
        self.assertEqual(EntryInteraction.objects.latest('connection__published').connection.title, "Point to launch new challenger bank with rewards on debit card purchases")
        self.assertEqual(Subscription.objects.first().last_updated.date(), datetime.datetime(2020, 7, 1, 18, 33, 37, 882000).date())
        self.client.post(reverse("feed:reload_all_feeds"), data={'page_type': 'index'})
        self.client.get(reverse("feed:index"))
        self.assertEqual(Subscription.objects.first().last_updated.date(), datetime.datetime.now().date())
        self.assertEqual(len(EntryInteraction.objects.all()), 40)
        self.assertEqual(EntryInteraction.objects.latest('connection__published').connection.title, "Extension rounds help some startups play offense during COVID-19")
    
    def test_reloading_updates_last_modified_of_SiteFeed(self, func_1, func_2):
        self.assertEqual(SiteFeed.objects.first().last_modified.date(), datetime.datetime(2020, 7, 1, 18, 33, 37, 882000).date())
        self.client.post(reverse("feed:reload_all_feeds"), data={'page_type': 'index'})
        self.assertEqual(SiteFeed.objects.first().last_modified.date(), datetime.datetime.now().date())        


class PagesAreMissingTheirCorrectItems(FixturesTestCase):
    def test_currently_reading_page_has_only_expected_items(self):
        index_page_response = self.client.get(reverse("feed:index"))
        currently_reading_page_response = self.client.get(reverse("feed:currently_reading"))
        entry = EntryInteraction.objects.first()
        self.assertContains(index_page_response, entry)
        self.assertNotContains(currently_reading_page_response, entry)
        self.client.post(reverse('feed:mark_as_currently_reading', args=[entry.pk]), data={'page_type': 'index'})
        index_page_response = self.client.get(reverse("feed:index"))
        currently_reading_page_response = self.client.get(reverse("feed:currently_reading"))
        self.assertNotContains(index_page_response, entry)
        self.assertContains(currently_reading_page_response, entry)

    @mock.patch('feed.feedTools.find_out_type', side_effect=fake_find_out_type)
    @mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser)
    def test_latest_page_is_missing_older_items(self, func_1, func_2):
        entry_that_should_not_be_in_latest = EntryInteraction.objects.first()
        self.client.post(reverse('feed:add_feed'), data={'url': 'example.org', 'page_type': 'index'})
        response_1 = self.client.get(reverse("feed:index"))
        self.assertContains(response_1, entry_that_should_not_be_in_latest)
        self.assertContains(response_1, "Entry 1")
        response_2 = self.client.get(reverse('feed:latest'))
        self.assertNotContains(response_2, entry_that_should_not_be_in_latest)
        self.assertContains(response_2, "Entry 1")

class EntryPageTests(FixturesTestCase):

    def test_uses_correct_template(self):
        entry = EntryInteraction.objects.first()
        response = self.client.get(reverse('feed:entry_page', args=[entry.pk]), data={'page_type': 'index'})
        self.assertTemplateUsed(response, "feed/entry.html")
    
    def test_page_contains_correct_info(self):
        entry = EntryInteraction.objects.first()
        response = self.client.get(reverse('feed:entry_page', args=[entry.pk]), data={'page_type': 'index'})
        self.assertContains(response, entry.connection.title[0:49])
        self.assertContains(response, entry.connection.content)