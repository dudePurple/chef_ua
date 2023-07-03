from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('add_or_update_order_item/<int:product_id>/', views.add_or_update_order_item, name='add_or_update_order_item'),
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('successful_payment/', views.successful_payment, name='success'),
    path('cancelled_payment/', views.cancelled_payment, name='cancel'),
    path('', views.product_list, name='product_list'),
]
