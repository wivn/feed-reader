from django.test import TestCase
import datetime
from feed.feedTools import check_feed
from feed.models import SiteFeed, Entry, Subscription
import feedparser
from unittest import mock 
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
class RSSFeedTest(TestCase):
    def test_handles_all_correct_properties_for_SiteFeed(self, func_1, func_2):
        check_feed(test_url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.url, test_url_base)
        self.assertEqual(feed.feed_url, test_url)
        self.assertEqual(feed.title, "Example Feed")
        # checks that both are the same day, since the mock doesn't return a last_modified time, it uses the current time
        self.assertEqual(feed.last_modified.date(), recent_date.date())
        self.assertEqual(feed.etag, None)        
    def test_handles_props_for_entries(self, func_1, func_2):
        check_feed(test_url)
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

h_entries_url = "https://www.example.org/"
h_entries_test_page = """<html><head><title>Testing Page</title></head><body><div><ul class="h-card"><li><a rel="me" href="mailto:admin@example.org" class="u-email">admin@example.org</a></li></ul></div><header><h1>Test Page</h1><h2>A testing ground</h2></header><main>    <article class="h-entry" id="entry_33fd648ff4c347f5aa37e61575bef3c4"> <div class="e-content">   <p class="like">Liked: <a href="https://www.example.org/wow">Wow what a cool page</a></p>                        </div>        <div>            <div>                <p>                    <time class="dt-published" datetime="2020-07-09 09:55:57 -0400" title="Thursday, July 9, 2020 9:55 AM EDT">July 9, 2020                    </time>                </p>            </div>            <div>                <p><a href="/2020/07/9/the-cool-page" class="u-url">Permalink</a></p>            </div>        </div>    </article>    <article class="h-entry" id="entry_f4546ce907a54221b039342205b76a2b"><p class="reply">In reply to: <a href="https://www.example.org/reply">Example dot org's reply site</a></p>        <div class="e-content">    <p>What an amazing reply this is</p>        </div>        <div>            <div>                <p>                    <time class="dt-published" datetime="2020-07-09 09:13:02 -0400" title="Thursday, July 9, 2020 9:13 AM EDT">July 9, 2020                    </time>                </p>            </div>            <div>                <p><a href="/2020/07/9/the-reply" class="u-url">Permalink</a></p>            </div>        </div>    </article></main></body></html>"""
@mock.patch('feed.feedTools.find_out_type', side_effect=lambda x: (None, h_entries_test_page, h_entries_url))
class HEntriesFeedTest(TestCase):
    def setUp(self):
        self.url = h_entries_url
    def test_handles_all_correct_properties_for_SiteFeed(self, func_1):
        check_feed(self.url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.url, h_entries_url)
        self.assertEqual(feed.feed_url, None)
        self.assertEqual(feed.title, "Testing Page")
        # checks that both are the same day, since the mock doesn't return a last_modified time, it uses the current time
        self.assertEqual(feed.last_modified.date(), recent_date.date())
        self.assertEqual(feed.etag, None)
    def test_handles_props_for_entries(self, func_1):
        check_feed(test_url)
        entries = Entry.objects.all()
        entry_1 = entries[0]
        self.assertEqual(entry_1.title, 'No title')
        self.assertEqual(entry_1.url, "https://www.example.org/2020/07/9/the-cool-page")
        self.assertEqual(entry_1.content, '<p>Liked: <a href="https://www.example.org/wow">Wow what a cool page</a></p>')
        self.assertEqual(entry_1.summary, None)
        self.assertEqual(entry_1.published.strftime("%Y-%m-%d %H:%M:%S.%f"), "2020-07-09 13:55:57.000000")
        self.assertEqual(entry_1.story_id, None)
        self.assertEqual(entry_1.feed, SiteFeed.objects.first())
        entry_2 = entries[1]
        self.assertEqual(entry_2.title, 'No title')
        self.assertEqual(entry_2.url, 'https://www.example.org/2020/07/9/the-reply')
        self.assertEqual(entry_2.content, '<p>What an amazing reply this is</p>')
        self.assertEqual(entry_2.summary, None)
        self.assertEqual(entry_2.published.strftime("%Y-%m-%d %H:%M:%S.%f"),'2020-07-09 13:13:02.000000')
        self.assertEqual(entry_2.story_id, None)
        self.assertEqual(entry_2.feed, SiteFeed.objects.first())
h_feed = """
<!DOCTYPE html>
<head><title>The Markup Blog Title Title</title></head>
<div class="h-feed hfeed">
  <h1 class="p-name site-title">The Markup Blog</h1>
  <p class="p-summary site-description">Stories of elements of their attributes.</p>
 
  <article class="h-entry hentry">
    <a class="u-url" rel="bookmark" href="latest/">
      <h2 class="p-name entry-title">Latest</h2>
    </a>
    <address class="p-author author h-card vcard">
      <a href="https://chandra.example.com/" class="u-url url p-name fn" rel="author">Chandra</a>
    </address>
    <time class="dt-published published" datetime="2012-06-22T09:45:57-07:00">June 21, 2012</time>
    <div class="p-summary entry-summary">
      <p>Super interesting</p>
    </div>
    <a href="/category/uncategorized/" rel="category tag" class="p-category">General</a>
  </article>
 
  <article class="h-entry hentry">
    <a class="u-url" rel="bookmark" href="oldest/">
      <h2 class="p-name entry-title">Old</h2>
    </a>
    <address class="p-author author h-card vcard">
      <a href="https://chandra.example.com/" class="u-url url p-name fn" rel="author">Chandra</a>
    </address>
    <time class="dt-published published" datetime="2012-06-20T08:34:46-07:00">June 20, 2012</time>
    <div class="p-summary entry-summary">
      <p>Super interesting, but from before.</p>
    </div>
    <a href="/category/uncategorized/" rel="category tag" class="p-category">General</a>
  </article>
 
</div>
</html>"""
@mock.patch('feed.feedTools.find_out_type', side_effect=lambda x: (None, h_feed, h_entries_url))
class HFeedTest(TestCase):
    def setUp(self):
        self.url = h_entries_url
    def test_handles_all_correct_properties_for_SiteFeed(self, func_1):
        check_feed(self.url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.url, h_entries_url)
        self.assertEqual(feed.feed_url, None)
        self.assertEqual(feed.title, "The Markup Blog")
        # checks that both are the same day, since the mock doesn't return a last_modified time, it uses the current time
        self.assertEqual(feed.last_modified.date(), recent_date.date())
        self.assertEqual(feed.etag, None)
    def test_handles_props_for_entries(self, func_1):
        check_feed(test_url)
        entries = Entry.objects.all()
        entry_1 = entries[0]
        self.assertEqual(entry_1.title, "Latest")
        self.assertEqual(entry_1.url, "https://www.example.org/latest/")
        self.assertEqual(entry_1.content, 'Super interesting')
        self.assertEqual(entry_1.summary, 'Super interesting')
        self.assertEqual(entry_1.published.strftime("%Y-%m-%d %H:%M:%S.%f"), "2012-06-22 16:45:57.000000")
        self.assertEqual(entry_1.story_id, None)
        self.assertEqual(entry_1.feed, SiteFeed.objects.first())
        entry_2 = entries[1]
        self.assertEqual(entry_2.title, 'Old')
        self.assertEqual(entry_2.url, 'https://www.example.org/oldest/')
        self.assertEqual(entry_2.content, 'Super interesting, but from before.')
        self.assertEqual(entry_2.summary, 'Super interesting, but from before.')
        self.assertEqual(entry_2.published.strftime("%Y-%m-%d %H:%M:%S.%f"),'2012-06-20 15:34:46.000000')
        self.assertEqual(entry_2.story_id, None)
        self.assertEqual(entry_2.feed, SiteFeed.objects.first())

h_entries_no_title_test_page = """<html><body><div><ul class="h-card"><li><a rel="me" href="mailto:admin@example.org" class="u-email">admin@example.org</a></li></ul></div><header><h1>Test Page</h1><h2>A testing ground</h2></header><main>    <article class="h-entry" id="entry_33fd648ff4c347f5aa37e61575bef3c4"> <div class="e-content">   <p class="like">Liked: <a href="https://www.example.org/wow">Wow what a cool page</a></p>                        </div>        <div>            <div>                <p>                    <time class="dt-published" datetime="2020-07-09 09:55:57 -0400" title="Thursday, July 9, 2020 9:55 AM EDT">July 9, 2020                    </time>                </p>            </div>            <div>                <p><a href="/2020/07/9/the-cool-page" class="u-url">Permalink</a></p>            </div>        </div>    </article>    <article class="h-entry" id="entry_f4546ce907a54221b039342205b76a2b"><p class="reply">In reply to: <a href="https://www.example.org/reply">Example dot org's reply site</a></p>        <div class="e-content">    <p>What an amazing reply this is</p>        </div>        <div>            <div>                <p>                    <time class="dt-published" datetime="2020-07-09 09:13:02 -0400" title="Thursday, July 9, 2020 9:13 AM EDT">July 9, 2020                    </time>                </p>            </div>            <div>                <p><a href="/2020/07/9/the-reply" class="u-url">Permalink</a></p>            </div>        </div>    </article></main></body></html>"""
h_feed_no_title = """
<!DOCTYPE html>
<div class="h-feed hfeed">
  <p class="p-summary site-description">Stories of elements of their attributes.</p>
 
  <article class="h-entry hentry">
    <a class="u-url" rel="bookmark" href="latest/">
      <h2 class="p-name entry-title">Latest</h2>
    </a>
    <address class="p-author author h-card vcard">
      <a href="https://chandra.example.com/" class="u-url url p-name fn" rel="author">Chandra</a>
    </address>
    <time class="dt-published published" datetime="2012-06-22T09:45:57-07:00">June 21, 2012</time>
    <div class="p-summary entry-summary">
      <p>Super interesting</p>
    </div>
    <a href="/category/uncategorized/" rel="category tag" class="p-category">General</a>
  </article>
 
  <article class="h-entry hentry">
    <a class="u-url" rel="bookmark" href="oldest/">
      <h2 class="p-name entry-title">Old</h2>
    </a>
    <address class="p-author author h-card vcard">
      <a href="https://chandra.example.com/" class="u-url url p-name fn" rel="author">Chandra</a>
    </address>
    <time class="dt-published published" datetime="2012-06-20T08:34:46-07:00">June 20, 2012</time>
    <div class="p-summary entry-summary">
      <p>Super interesting, but from before.</p>
    </div>
    <a href="/category/uncategorized/" rel="category tag" class="p-category">General</a>
  </article>
 
</div>
</html>"""
test_page_no_title = f"""<feed xmlns="http://www.w3.org/2005/Atom"><generator uri="https://jekyllrb.com/" version="3.8.5">Jekyll</generator><link href="https://www.example.org/feed.xml" rel="self" type="application/atom+xml"/><link href="https://www.example.org/" rel="alternate" type="text/html"/><updated>2020-06-29T16:00:05+00:00</updated><id>https://www.example.org/feed.xml</id><author><name>Example Writer</name></author><entry><title type="html">Entry 1</title><link href="https://www.example.org/1" rel="alternate" type="text/html" title="Entry 1"/><published>{recent_date}</published><updated>{recent_date}</updated><id>https://www.example.org/1</id><content type="html" xml:base="https://www.example.org/1">hello 1</content><author><name>Example Writer</name></author><summary type="html"/></entry><entry><title type="html">Entry 2</title><link href="https://www.example.org/2" rel="alternate" type="text/html" title="Entry 2"/><published>{old_date}</published><updated>{old_date}</updated><id>https://www.example.org/2</id><content type="html" xml:base="https://www.example.org/2">hello 2</content><author><name>Example Writer</name></author><summary type="html">hello 2</summary></entry></feed>"""
test_feed_no_title = feedparser.parse(test_page_no_title)
def fake_feed_parser_no_title(a, *args, **kwargs):
  return test_feed_no_title
class HandlesNoTitleCorrectly(TestCase):
    @mock.patch('feed.feedTools.find_out_type', side_effect=lambda x: (None, h_entries_no_title_test_page, h_entries_url))
    def test_handles_h_entries(self, func_1):
        check_feed(h_entries_url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.title, "No Title")
    @mock.patch('feed.feedTools.find_out_type', side_effect=lambda x: (None, h_feed_no_title, h_entries_url))
    def test_handles_h_feed(self, func_1):
        check_feed(h_entries_url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.title, "No title for feed")
      
    @mock.patch('feed.feedTools.find_out_type', side_effect=lambda x: (test_url, test_page_no_title , test_url))
    @mock.patch('feed.feedTools.feedparser.parse', side_effect=fake_feed_parser_no_title)
    def test_handles_rss_feed(self, func_1, func_2):
        check_feed(test_url)
        feed = SiteFeed.objects.first()
        self.assertEqual(feed.title, "No title")