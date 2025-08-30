from django.urls import path
from .views import get_products_by_category, get_products_by_search, get_categories, stream_drive_image, best_deals_view, get_banners

urlpatterns = [
    path('get_products/', get_products_by_category),
    path("search_products/", get_products_by_search, name="search_products"),
    path("get_categories/", get_categories),
    path("images/", stream_drive_image, name="stream_google_image"),
    path("best_deals/", best_deals_view),
    path("banners/", get_banners)
]