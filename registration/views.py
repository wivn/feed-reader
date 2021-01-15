from django.contrib.auth import views as auth_views
from django.contrib.auth import login, authenticate
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator

User = get_user_model()

def redirect_logged_in_users(function):
    def _function(request,*args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("feed:index")) 
        return function(request, *args, **kwargs)
    return _function

@method_decorator(redirect_logged_in_users, name='dispatch')
class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'

class LogoutView(auth_views.LogoutView):
	template_name = 'registration/logout.html'

@redirect_logged_in_users
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

