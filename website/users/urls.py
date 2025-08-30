from django.urls import path
from .views import *

urlpatterns = [
    path('profile_details/', get_user_profile_view),
    path('address/add_address/', add_address),
    path('address/get_addresses/',get_addresses),
    path('address/delete_address/', delete_address),
    path('address/edit_address/', edit_address),
    path("add_to_wishlist/", add_to_wishlist),
    path("remove_from_wishlist/", remove_from_wishlist),
    path("wishlist/", get_wishlist),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/remove/", remove_from_cart, name="remove_from_cart"),
    path("cart/", get_cart, name="get_cart"),
    path("cart/update-quantity/", update_cart_quantity, name="update_cart_quantity"),
]