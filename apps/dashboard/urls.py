from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.dashboard_page, name='dashboard_page'),
]