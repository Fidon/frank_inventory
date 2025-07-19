from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.crips_page, name='crips_page'),
    path('actions/', v.crips_actions, name='crips_actions'),
    path('<int:crip_id>/', v.crips_details, name='crips_details'),
]