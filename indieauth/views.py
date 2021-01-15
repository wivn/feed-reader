from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
from urllib.parse import urlencode, unquote
import requests
from bs4 import BeautifulSoup
from django.utils.crypto import get_random_string
from django.contrib import messages
from urllib.parse import urlparse, urljoin
from django.contrib.auth import get_user_model
from django.contrib.auth import login as login_auth

def redirect_logged_in_users(function):
    def _function(request,*args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("feed:index")) 
        return function(request, *args, **kwargs)
    return _function

@redirect_logged_in_users
def index(request):
	cleanup(request)
	return render(request, 'indieauth/index.html', {})
def login(request):
	try:
		if request.method == 'POST':
			site = request.POST.get("site", None)
			url_data = urlparse(site)
			
			if site and url_data.netloc != '' and (url_data.scheme == 'http' or url_data.scheme == 'https'):
				if url_data.path == '':
					site = site + '/'
					print(site)
				r = requests.get(site)
				soup = BeautifulSoup(r.text, 'html.parser')
				unique_id = get_random_string(length=32)
				for link in soup.find_all('link'):
					if link.get('rel')[0] == "authorization_endpoint":
						authorization_endpoint = link.get('href')
						# if relative URL, this will attach it to the end of the redirected url
						authorization_endpoint = urljoin(r.url, authorization_endpoint)
				if r.headers.get('Link', None):
					links = r.headers['Link']
					print(links)
					for link in links.split(","):
						possible_url = link.split(";")[0].strip()
						possible_url = possible_url[1:len(possible_url)-1]
						possible_rel = link.split(";")[1].strip()
						if possible_rel == "rel=authorization_endpoint":
							authorization_endpoint = urljoin(r.url, possible_url)
				# after redirects, the final URL will be contained in the  response
				site = r.url
				print(r.history)
				searchHistory = True
				i = -1
				# ensure that if there's temp redirects that the "me" url is always the last permanent redirect
				while searchHistory and (i*-1) <= len(r.history):
					history_piece = r.history[i]
					if history_piece.status_code == 301:
						site = history_piece.url
					i -= 1
				# If ALL of them are temporary redirects than use the initial value
				if all(i.status_code == 302 for i in r.history):
					site = request.POST.get("site", None)
				if authorization_endpoint:
					request.session['authorization_endpoint']=authorization_endpoint
					request.session['client_id'] = site
					request.session['state'] = unique_id
					payload = {'me': site, 
						'redirect_uri': request.build_absolute_uri(reverse('indieauth:redirect')),
						 'client_id': f'{request.scheme}://{ request.get_host() }/indieauth/application_info', 
						 'state': unique_id,
						 'response_type': 'id'}
					redirect_site = authorization_endpoint + "?" + urlencode(payload)
					return HttpResponseRedirect(redirect_site)
				else:
					cleanup(request)
					messages.error(request, 'No authorization_endpoint found.')
					return HttpResponseRedirect(reverse('indieauth:index'))
	except Exception as e:
		print(e)
		messages.error(request, 'Error in retrieving url.')
		return HttpResponseRedirect(reverse('indieauth:index'))
	messages.error(request, 'No site submitted or the URL submitted was not valid.')
	return HttpResponseRedirect(reverse('indieauth:index'))

def redirect(request):
	if request.GET.get('state', None) == request.session.get('state', None) and request.session.get('state', None) != None:
		client_id = request.session['client_id']
		authorization_endpoint = request.session['authorization_endpoint']
		redirect_uri = request.build_absolute_uri(reverse('indieauth:redirect'))

		code = request.GET.get('code')
		r = requests.post(authorization_endpoint, data = {'code':code, 'client_id':client_id, 'redirect_uri': redirect_uri})
		if r.headers['content-type'] == "application/x-www-form-urlencoded":
			user_site = unquote(r.text)[3:]
		elif r.headers['content-type'] == "application/json":
			user_site = r.text['me']
		else:
			user_site = None
		user_site_matches_domain = urlparse(client_id).netloc == urlparse(user_site).netloc
		print(urlparse(client_id).netloc, urlparse(user_site).netloc)
		if r.status_code == 200 and user_site and user_site_matches_domain:
			messages.success(request, 'Your URL is: ' + user_site)
			user_model = get_user_model()
			user = user_model.objects.filter(site=user_site)
			if user:
				login_auth(request, user[0])
			else:
				user = user_model.objects.create_user(username=user_site, site=user_site)
				user.set_unusable_password()
				login_auth(request, user)

			cleanup(request)
			return HttpResponseRedirect(reverse('feed:index'))
		else:
			messages.error(request, 'Error in URL. Please try again.')
			cleanup(request)
			return HttpResponseRedirect(reverse('indieauth:index'))
	else:
		messages.error(request, 'Major error. Likely timeout. Please try again.')
		cleanup(request)
		return HttpResponseRedirect(reverse('indieauth:index'))

def cleanup(request):
	try:
		del request.session['authorization_endpoint']
		del request.session['state']
		del request.session['client_id']
	except KeyError:
		pass

def application_info(request):
	return render(request, "indieauth/application_info.html")