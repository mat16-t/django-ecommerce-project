# orders/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import place_order, order_view

# router = DefaultRouter()
# router.register(r'orders', OrderViewSet)

app_name = 'orders'

urlpatterns = [
    # path('api/', include(router.urls)),
    path('place-order/', place_order, name='place-order'),
    path('order/', order_view, name='view-order'),
    # path()

]
