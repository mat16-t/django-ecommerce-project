# orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer  # Assuming you have a ProductSerializer in the products app

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # You can use more detailed user data if necessary
    order_items = OrderItemSerializer(source='orderitem_set', many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'order_items', 'total_amount', 'status', 'created_at', 'updated_at']
