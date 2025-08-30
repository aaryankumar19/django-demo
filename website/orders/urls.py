from django.urls import path
from .views import create_order_view, review_order_view, get_user_orders_view, order_details_view

urlpatterns = [
    path('place-order/', create_order_view),
    path('order-summary/', review_order_view),
    path('order-history/', get_user_orders_view),
    path('order-details/<int:order_id>/',order_details_view),
]