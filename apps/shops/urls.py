from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.shops_page, name='shops_page'),
    path('actions/', v.shops_requests, name='shop_actions'),
    path('<int:shopid>/', v.shop_details, name='shop_details'),
]
