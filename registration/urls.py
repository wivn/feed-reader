from django.urls import path

from . import views
from django.contrib.auth import views as auth_views

app_name = 'registration'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]
