from django.urls import path
from .views import CategoryListView, ProductListView, ProductDetailView
from .api_views import api_products_by_category, api_product_detail

app_name = 'products'

urlpatterns = [
    path('api/categories/', CategoryListView.as_view(), name='category-list'),
    path('api/categories/<str:category>/', api_products_by_category, name='api-products-by-category'),
    path('api/products/<slug:slug>/', api_product_detail, name='api-product-detail'),
]
