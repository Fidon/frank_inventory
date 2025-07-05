from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import LoginForm
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render


@require_POST
def authenticate_user(request):
    form = LoginForm(request.POST)

    if form.is_valid():
        user = form.user
        login(request, user)
        next_url = request.POST.get('next_url', reverse('dashboard_page'))
        response = JsonResponse({'success': True, 'url': next_url})
        response.set_cookie('username', user.username) 
        return response

    error_msg = form.errors['__all__'][0]
    return JsonResponse({'success': False, 'sms': error_msg, 'error': form.errors})

def signout_page(request):
    if request.user.is_authenticated:
        logout(request)
        response = redirect(reverse('index_page'))
        response.delete_cookie('username')
        return response
    return redirect(reverse('dashboard_page'))