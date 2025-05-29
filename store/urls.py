from django.urls import path, include
from .views import home, category_products, product_detail, add_to_cart, cart_view, update_cart_quantity, place_order, product_list, add_or_update_product, search_products, product_search_view, suggest_view, add_to_compare, compare_view, remove_from_compare

app_name = 'store'

urlpatterns = [
    path('', home, name='home'),
    path('category/<slug:slug>/', category_products, name='category-products'),
    path('product/<slug:slug>/', product_detail, name='product-detail'),
    path('add-to-cart/<str:product_id>/', add_to_cart, name='add-to-cart'),
    path('cart/', cart_view, name='view-cart'),
    path('update-cart/', update_cart_quantity, name='update-cart'),
    path('place-order/', place_order, name='place-order'),
    path('product-list/',product_list, name='product-list'),
    path("admin/product/", product_list, name="admin_product_list"),
    path("add-product/", add_or_update_product, name="add-product"),
    # path("add-product-variant/<str:product_id>/", add_product_variant, name="add-product-variant"),
    path("api/search/", search_products, name="search-products"),
    path("search-products/", product_search_view, name="product-search"),
    path('api/suggest/', suggest_view, name='suggest'),
    path('add-compare/', add_to_compare, name='add-to-compare'),
    path('compare/', compare_view, name='compare-view'),
    path('remove-from-compare/<str:product_id>/', remove_from_compare, name='remove-from-compare'),
]
