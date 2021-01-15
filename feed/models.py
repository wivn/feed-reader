from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
class FeedlessEntry(models.Model):
	url = models.TextField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	def __str__(self):
		return self.url

class SiteFeed(models.Model):
	url = models.TextField()
	title = models.TextField(null=True, blank=True)
	feed_url = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	last_modified = models.DateTimeField(auto_now_add=True, blank=True, null=True)
	etag = models.TextField(null=True, blank=True)
	def __str__(self):
		if self.feed_url:

			return self.url + "-" + self.feed_url
		else:
			return self.url
class Entry(models.Model):
	url = models.TextField()
	title = models.TextField()
	content = models.TextField(null=True, blank=True)
	summary = models.TextField(null=True, blank=True)
	published = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	story_id = models.TextField(null=True, blank=True)
	feed = models.ForeignKey(SiteFeed, on_delete=models.CASCADE, null=True)
	

	def __str__(self):
		return self.title
# this is how user's will subscribe to a feed, create the site feed on addition
# or subscribe user
class Subscription(models.Model):
	feed = models.ForeignKey(SiteFeed, on_delete=models.CASCADE)
	last_updated = models.DateTimeField(null=True, blank=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	def __str__(self):
		return self.feed.title

class EntryInteraction(models.Model):
	connection = models.ForeignKey(
        Entry, on_delete=models.CASCADE)
	read = models.BooleanField(default=False)
	currently_reading = models.BooleanField(default=False)
	sub = models.ForeignKey(Subscription, on_delete=models.CASCADE)
	def __str__(self):
		return self.connection.title


