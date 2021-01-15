from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from .models import Entry, SiteFeed, Subscription, EntryInteraction, FeedlessEntry
import feedparser
import mf2py
import datetime
import requests
import re
import html
import urllib.parse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc
from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.html import strip_tags
import bleach
from django.contrib import messages
from .urlsOnPage import urlsOnPage
from .utils import schemeify_url
from django.contrib import messages
from dateutil import parser
max_mins_until_reload_feed = 5

def dfs(nodes):
    if nodes is not None:
        for node in nodes:
            yield node
            if 'children' in node:
	            for child in dfs(node['children']):
	                yield child



def get_hfeed(url, text):
	obj = mf2py.parse(doc=text)
	for node in dfs(obj['items']):
		if 'h-feed' in node['type']:
			html_title = re.search('<title[^>]*>([^<]+)</title>', text)
			if html_title:
				html_title = html_title.group(1)
				html_title = html.unescape(html_title)
			else:
				html_title = "No title for feed"
			
			children_data = node['children']
			final_title = node["properties"].get("name", html_title)
			print("GIVE ME THE TITLE", final_title)
			if isinstance(final_title, list): 
				final_title = final_title[0]
			return (children_data, final_title)
		#print(obj['items'][0]["children"][0])

def get_hentries(url, text):
	obj = mf2py.parse(doc=text)
	feed = []
	for node in dfs(obj['items']):
		if 'h-entry' in node['type']:
			feed.append(node)
	
	html_title = re.search('<title[^>]*>([^<]+)</title>', text)
	
	if html_title:
		html_title = html_title.group(1)
		html_title = html.unescape(html_title)
	else:
		html_title = "No Title"
	return (feed, obj.get("properties", {}).get("name", html_title))

def parse_hfeed(url, text):
	# need feed_title
	# feed_link is just url
	try:
		feed, feed_title = get_hfeed(url, text)
	except:
		feed, feed_title = get_hentries(url, text)
		# if the feed is empty then this error will be called
	print(feed_title)
	entries = []
	i = 0
	for entry in feed:
		if 'h-entry' in entry['type'] and "properties" in entry:
			e_props = entry.get("properties", None)
			link = e_props.get("url", None)
			if isinstance(link, list):
				link = link[0]
			link = urllib.parse.urljoin(url, link)


			# need a url at least to save something
			if e_props and link:
				title = e_props.get("name", "No title")
				if isinstance(title, list):
					title = title[0]
				story_id = e_props.get("uid", None)
				if isinstance(story_id, list):
					story_id = story_id[0]
				published = e_props.get("published", datetime.datetime.utcnow().replace(tzinfo=utc))
				if isinstance(published, list):
					published = published[0]
				# if the current datetime doesn't work try another one, if that one doesn't work then return the current time
				if isinstance(published, str):
					if parse_datetime(published) == None:
						try:
							published = datetime.datetime.strptime(published, "%d %b %Y").date()
						except:
							published = datetime.datetime.utcnow().replace(tzinfo=utc)

				content = e_props.get("content", e_props.get("summary", None))
				if isinstance(content, list):
					content = content[0]
					if isinstance(content, dict):
						content = content['html']
				summary = e_props.get("summary", None)
				if isinstance(summary, dict):
					summary = summary[0]
				if isinstance(summary, list):
					summary = summary[0]
				entryParsed = {
					"title": title, 
					"id": story_id, 
					"published": published, 
					"link": link, 
					"content": content, 
					"summary": summary
				}
				entries.append(entryParsed)
	return {"entries": entries, "feed_title": feed_title, "feed_link": url, "etag": None, "last_modified": timezone.now(), "feed_url": None}			

def subscribe_websub(url):
	pass
def parse(url, feed_url, page_text, etag=None, modified=None):
	if feed_url:
		data = parse_feed(feed_url, etag, modified)
		# if the feed didn't work try the h_feed
		if data:
			return data
		else:
			h_data = parse_hfeed(url, page_text)
			print(h_data)
			return h_data
	else:
		# i save a request if it's an h-feed, but if it's an RSS feed I need to make another request due to etag and last modified
		# really this request should just get me the headers, BUT then I'd have to check the text anyways for an RSS link
		return parse_hfeed(url, page_text)
def find_out_type(url):
	p = schemeify_url(url)
	r = requests.get(p)
	if "application/xml" in r.headers['content-type']:
		return (url, r.text, url)
	else:
		if feedparser.parse(r.text).bozo == 0:
			return (url, r.text, url)
		soup = BeautifulSoup(r.text, 'html.parser')
		for link in soup.find("head").find_all('link'):
			if link.get('type') == "application/atom+xml":
				return (link.get('href'), r.text, r.url)
			elif link.get('type') == "application/rss+xml":
				return (link.get('href'), r.text, r.url)
			# if it is a valid feed
		
		# if the original url hasn't been returned as an RSS feed or the link of the feed returned, then there is no feed url
		return (None, r.text, r.url)

def clean(doc):
	return bleach.clean(doc, tags= ['a', 'abbr', 'div', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'strong', 'ul', 'img', 'p', 'span', 'br'],
		attributes={'a': ['href', 'title'], 'abbr': ['title'], 'acronym': ['title'], 'img': ['alt', 'src']})

# ONLY THIS FUNCTION IS ACTUALLY EXPOSED, so the internals can be safetly modified
def check_feed(url):
	# get url and take etag and last modified
	# if it doesn't exist then don't

	# use Content-Type to see if I should use the h-feed parser or the RSS parser
		# if I do this then pass the request that way I don't call it again
	print(url)
	try:
		feed_url, page_text, url = find_out_type(url)
	except:
		return None
	try:
		# pass etag and last mofidied
		feed = SiteFeed.objects.get(url=url, feed_url=feed_url)
		# if last modified is within the past 10 minutes, don't update it
		now = datetime.datetime.now()
		diff_in_time = now - feed.last_modified
		if (diff_in_time.total_seconds() / 60) < max_mins_until_reload_feed:
			print("don't update")
			return

		data = parse(feed.url, feed.feed_url, page_text, feed.etag, feed.last_modified)
		# if it exists and it's empty it means there's been no changes so return
		if len(data["entries"]) == 0:
			return
	except:
		data = parse(url, feed_url, page_text)
			
	# ASSUMPTION: Make URL doesn't change
	try:
		try:
			feed, created = SiteFeed.objects.update_or_create(
				url=data["feed_link"], feed_url=data["feed_url"],

				defaults={'title':data["feed_title"],
				'last_modified': parser.parse(data['last_modified']),
				'etag':data["etag"]},

			)
		# date error
		except:
			feed, created = SiteFeed.objects.update_or_create(
				url=data["feed_link"], feed_url=data["feed_url"],

				defaults={'title':data["feed_title"],
				'last_modified': data['last_modified'],
				'etag':data["etag"]},

			)
		print("data, " ,data['last_modified'])
		for entry in data["entries"]:
			# add if an entry with that URL doesn't exist
			# ASSUMPTION: URLs for entries remain static
			if entry['summary']:
				summary = strip_tags(entry['summary'])
			else:
				summary = entry['summary']
			try:
				
				obj_entry, created_entry = Entry.objects.update_or_create(
					url=entry["link"],
					defaults={'title':clean(entry["title"]),
							'feed':feed, 
							'story_id':entry["id"], 
							'published':entry["published"],
							'content': clean(entry["content"]),
							'summary': summary}
				)
			# if there is a date error
			except:
				obj_entry, created_entry = Entry.objects.update_or_create(
					url=entry["link"],
					defaults={'title':clean(entry["title"]),
							'feed':feed, 
							'story_id':entry["id"], 
							'published':parser.parse(entry["published"]),
							'content': clean(entry["content"]),
							'summary': summary }
				)

		return feed
	except Exception as e:
		print(e)
		return None


# parse feed
# parse feed on reload
# check for etag and update etag (OR last modified)
# it will add everything in entries (which will be empty if the etag was the same)
# before it adds something it checks if it exists
	

def parse_feed(url, etag=None, modified=None):
	d = feedparser.parse(url, etag=etag, modified=modified)
	if d.bozo == 0:
		feed_title = d.feed.get('title', 'No title')
		feed_link = d.feed.get('link', None)
		last_modified = d.get('modified', timezone.now())
		etag = d.get('etag', None)
		if 'entries' in d:
			entries = []
			for entry in d.entries:
				title = entry.get('title', 'No title')
				link = entry.get('link', None)
				entry_id = entry.get('id', None)

				published = entry.get('published', datetime.datetime.utcnow().replace(tzinfo=utc))

				try:
					content = entry.get('content', None)[0].value
				except:
					try:
						# or entry.content if not Atom feed
						content = entry.get('content')
					except:
						content = None
				summary = entry.get('summary', None)
				entryParsed = {
					"title": title, 
					"id": entry_id, "published": published, 
					"link": link, "content": content, "summary": summary
				}
				entries.append(entryParsed)
		return {"entries": entries, "feed_title": feed_title, "feed_link": feed_link, "etag": etag, "last_modified": last_modified, "feed_url": url}
	else:
		print("malformed feed")
		print(url)
		return None

