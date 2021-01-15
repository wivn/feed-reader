from django.urls import path
from . import views
app_name = "indieauth"
urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login, name='login'),
    path('redirect', views.redirect, name='redirect'),
    path('application_info', views.application_info, name='application_info'),
]
