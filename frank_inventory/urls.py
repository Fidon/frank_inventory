from django.contrib import admin
from django.urls import include, path
from . import views as v

handler404 = 'frank_inventory.views.error_404'
handler403 = 'frank_inventory.views.error_403'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', v.index_page, name='index_page'),
    path('users/', include('apps.users.urls')),
    path('shops/', include('apps.shops.urls')),
    path('crips/', include('apps.crips.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]
