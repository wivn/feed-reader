from django.urls import path
from . import views
app_name = "feed"
urlpatterns = [
    path('', views.index, name='index'),
    path('entry/<int:pk>/', views.entry_page, name='entry_page'),
    path('feed/new', views.add_feed, name='add_feed'),
    path('feed/reload', views.reload_all_feeds, name='reload_all_feeds'),
    path('feed/delete', views.delete_subscription, name='delete_subscription'),
    path('feed/entryinteraction/<int:pk>/read', views.change_entry_read_status, name='change_entry_read_status'),
    path('latest/', views.latest, name='latest'),
    path('current/', views.currently_reading, name='currently_reading'),
    path('feed/entryinteraction/<int:pk>/currently_reading', views.mark_as_currently_reading, name='mark_as_currently_reading'),
    path('feed/utils/find_urls_on_page', views.save_urls_from_page, name='save_urls_from_page'),
    path('feed/utils/find_urls_on_page/confirmation', views.save_urls_from_page_confirmation, name='save_urls_from_page_confirmation'),
    path('feed/utils/find_urls_on_page/confirm_urls', views.save_urls_from_page_confirm_urls, name='save_urls_from_page_confirm_urls'),
    path('feed/temp_urls/delete', views.delete_from_temp_urls_session, name='delete_from_temp_urls_session'),
    path('feed/feedlessentry/<int:pk>/delete', views.feedless_entry_deletion, name='feedless_entry_deletion')
]
