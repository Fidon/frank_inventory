from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required


@never_cache
def index_page(request):
    if request.user.is_authenticated:
        response = redirect(reverse('dashboard_page'))
        response.set_cookie('username', request.user.username)
        return response
    return render(request, 'index.html')

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_403(request, exception):
    return render(request, '403.html', status=403)
