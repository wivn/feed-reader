from django.contrib import admin
from .feedTools import check_feed
from .models import Entry, SiteFeed, Subscription, EntryInteraction
def force_reload_feed(modeladmin, request, queryset):
    for feed in queryset:
    	# note that there is the same version of this in the reload feeds function in views.py
    	if feed.feed_url:
    		check_feed(feed.feed_url)
    	else:
    		check_feed(feed.url)

force_reload_feed.short_description = "Force a feed to reload"

class EntryAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at',)

class SiteFeedAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)
    actions = [force_reload_feed]

admin.site.register(Entry, EntryAdmin)
admin.site.register(SiteFeed, SiteFeedAdmin)
admin.site.register(Subscription)
admin.site.register(EntryInteraction)