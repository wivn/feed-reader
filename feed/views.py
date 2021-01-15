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
from .feedTools import check_feed
from django.contrib.auth.decorators import login_required
max_mins_until_reload_feed = 5

@login_required
def feedless_entry_deletion(request, pk):
	if request.method == "POST":
		if pk:
			get_object_or_404(FeedlessEntry, user=request.user, pk=pk).delete()
	return HttpResponseRedirect(reverse('feed:currently_reading'))
"""
When you load the page, 
see if any of the feeds have been updated 
since that feeds last been checked by the user. 
If it has, get that feed’s newest posts after that 
time and create entries for the user.
"""
@login_required
def delete_from_temp_urls_session(request):
	if request.POST.get("url_to_delete_index", None) != None:
		
		index = int(request.POST["url_to_delete_index"])
		if request.session.get("temp_urls", None) != None:
			request.session["temp_urls"].pop(index)
			request.session.save()
	return HttpResponseRedirect(reverse('feed:save_urls_from_page_confirmation'))
@login_required
def save_urls_from_page_confirm_urls(request):
	if request.method == "POST" and request.session.get("temp_urls", None) != None:
		entries = [FeedlessEntry(url=url, user=request.user) for url in request.session['temp_urls']]
		FeedlessEntry.objects.bulk_create(entries)
		del request.session["temp_urls"]
	return HttpResponseRedirect(reverse('feed:currently_reading'))
@login_required
def save_urls_from_page_confirmation(request):
	return render(request, "feed/urls_on_page_confirmation.html", {'possible_urls': request.session["temp_urls"]})

@login_required
def save_urls_from_page(request):
	if request.method == "POST":
		url = request.POST["urls_from_page"]
		try:
			urls = urlsOnPage(schemeify_url(url))
			if urls == []:
				request.session['temp_urls'] = None
				del request.session["temp_urls"]
				messages.error(request, 'The webpage you submitted has no URLs on it.')
				return HttpResponseRedirect(reverse('feed:currently_reading'))
			request.session['temp_urls'] = urls
		except ValueError:
			request.session['temp_urls'] = None
			del request.session["temp_urls"]
			messages.error(request, 'There was a problem processing that URL. Please enter a valid URL and try again later.')
			return HttpResponseRedirect(reverse('feed:currently_reading'))
		return HttpResponseRedirect(reverse('feed:save_urls_from_page_confirmation'))
@login_required
def check_subs(request):
	subscriptions = Subscription.objects.filter(user=request.user)

	for sub in subscriptions:
		if sub.feed.last_modified != sub.last_updated:
			# add entries
			# set sub last_updated to last_modified
			if not sub.last_updated:
				check_since = datetime.date.min
			else:
				check_since = sub.last_updated

			new_entries = Entry.objects.filter(feed=sub.feed, created_at__gte=check_since)
			for new_entry in new_entries:
				EntryInteraction.objects.get_or_create(connection=new_entry, sub=sub)
				
			sub.last_updated = sub.feed.last_modified
			sub.save()
	return subscriptions
@login_required
def index(request):
	subscriptions = check_subs(request)

	entries = EntryInteraction.objects.filter(currently_reading=False, sub__user=request.user).order_by('-connection__published').select_related('connection')

	paginator = Paginator(entries, 15)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'feed/index.html', {"entries": page_obj, "subs": subscriptions})

@login_required
def latest(request):
	subscriptions = check_subs(request)
	date = datetime.datetime.now()
	start_date = date + datetime.timedelta(-date.weekday(), weeks=-1)
	entries = EntryInteraction.objects.filter(currently_reading=False, sub__user=request.user, connection__published__gte=start_date).order_by('-connection__published').select_related('connection')

	paginator = Paginator(entries, 15)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	return render(request, 'feed/index.html', {"entries": page_obj, "subs": subscriptions, "page_type": "latest"})

@login_required
def currently_reading(request):
	entries = EntryInteraction.objects.filter(currently_reading=True, sub__user=request.user).order_by('-connection__published').select_related('connection')
	feedless_urls = FeedlessEntry.objects.filter(user=request.user)
	paginator = Paginator(entries, 15)

	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	return render(request, 'feed/currently_reading.html', {"entries": page_obj, "feedless_urls": feedless_urls, "page_type": "currently_reading"})

@login_required
def mark_as_currently_reading(request, pk):
	if request.method == 'POST':
		if pk:
			entry_interaction = get_object_or_404(EntryInteraction, sub__user=request.user, pk=pk)
			entry_interaction.currently_reading = not entry_interaction.currently_reading
			entry_interaction.save() 
	return latest_or_index(request.POST.get("page_type", None))

def latest_or_index(page_type):
	print(page_type)
	if page_type == 'latest':
		return HttpResponseRedirect(reverse('feed:latest'))
	elif page_type == 'currently_reading':
		return HttpResponseRedirect(reverse("feed:currently_reading")) 
	else:
		return HttpResponseRedirect(reverse('feed:index')) 

@login_required
def add_feed(request):
	if request.method == 'POST':
		url = request.POST.get("url", None)
		if url:
			try:
				feed = check_feed(url)
				if feed:
					obj = Subscription(feed=feed, user=request.user)
					obj.save()
				else:
					messages.error(request, 'Site did not work.')
			except:
				messages.error(request, "Error with site's feed")
			return latest_or_index(request.POST.get("page_type", None))

	return latest_or_index(request.POST.get("page_type", None))

@login_required
def delete_subscription(request):
	if request.method == 'POST':
		pk = request.POST.get("id", None)
		if pk:
			sub = get_object_or_404(Subscription, user=request.user, pk=pk)
			sub.delete()
	return latest_or_index(request.POST.get("page_type", None))

@login_required
def reload_all_feeds(request):
	if request.method == "POST":
		subscriptions = Subscription.objects.filter(user=request.user)
		for sub in subscriptions:
			if sub.feed.feed_url:
				check_feed(sub.feed.feed_url)
			else:
				check_feed(sub.feed.url)
	return latest_or_index(request.POST.get("page_type", None))

@login_required
def entry_page(request, pk):
	entry = get_object_or_404(Entry, pk=pk)
	return_page_number = request.GET.get('return_page')
	page_type = request.GET.get('page_type')
	return render(request, 'feed/entry.html', {"entry": entry, "return_page": return_page_number, "page_type":page_type})

@login_required
def change_entry_read_status(request, pk):
	if request.method == 'POST':
		if pk:
			entry_interaction = get_object_or_404(EntryInteraction,sub__user=request.user, pk=pk)
			entry_interaction.read = not entry_interaction.read
			entry_interaction.save() 
	return latest_or_index(request.POST.get("page_type", None))