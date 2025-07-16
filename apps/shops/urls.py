from django.urls import path
from . import views as v

urlpatterns = [
    path('', v.shops_page, name='shops_page'),
    path('actions/', v.shops_requests, name='shop_actions'),
    path('<int:shopid>/', v.shop_details, name='shop_details'),
    path('products/', v.products_page, name='products_page'),
    path('products/actions/', v.products_requests, name='product_actions'),
    path('products/<int:itemid>/', v.product_details, name='product_details'),
    path('sales/', v.sales_page, name='sales_page'),
    path('sales/actions/', v.sales_actions, name='sales_actions'),
    path('sales/report/', v.sales_report, name='sales_report'),
    path('sales/report/sale-items/', v.sales_items_report, name='sale_items_report'),
]
