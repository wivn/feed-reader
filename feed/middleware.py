from django.shortcuts import redirect, reverse
from django.urls import resolve
class RedirectIfAddingURLsFromPageIsIncompleteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        excludedURLs = [reverse("feed:save_urls_from_page_confirmation"), 
            reverse("feed:save_urls_from_page_confirm_urls"), 
            reverse("feed:delete_from_temp_urls_session",),
            reverse("registration:logout")]
        path = f'/{resolve(request.path_info).route}'
        isExcludedURL = any([url == path for url in excludedURLs])
        if request.session.get("temp_urls", None) != None and not isExcludedURL:
            return redirect("feed:save_urls_from_page_confirmation")