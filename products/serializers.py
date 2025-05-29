from rest_framework import serializers
from products.models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# class ProductSerializer(serializers.ModelSerializer):
#     category = CategorySerializer(read_only=True)

#     class Meta:
#         model = Product
#         fields = '__all__'


class ProductVariantSerializer(serializers.Serializer):
    variant_id = serializers.CharField()
    storage = serializers.CharField(allow_null=True, required=False)
    ram = serializers.CharField(allow_null=True, required=False)
    color = serializers.CharField()
    price = serializers.FloatField()
    stock = serializers.IntegerField()
    image_url = serializers.CharField()

class ProductSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    brand = serializers.CharField()
    specifications = serializers.JSONField()
    variants = ProductVariantSerializer(many=True)
