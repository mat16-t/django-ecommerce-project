from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from django.core.cache import cache
import time

@api_view(['GET'])
def api_products_by_category(request, category):
    start_time = time.time()
    cache_key = f"api_category_{category.lower()}"
    cached_response = cache.get(cache_key)
    if cached_response:
        return Response({
            "data": cached_response,
            "cache": False,
            "response_time": duration
            })

    products = Product.objects(category__iexact=category)
    serializer = ProductSerializer(products, many=True)
    cache.set(cache_key, serializer.data, timeout=300)
    # end_time = time.time()
    duration = time.time() - start_time
    return Response({
        "data": serializer.data,
        "cache": True,
        "response_time": duration
        })


@api_view(['GET'])
def api_product_detail(request, slug):
    start_time = time.time()

    cache_key = f"api_product_{slug.lower()}"
    cached_product = cache.get(cache_key)
    if cached_product:
        duration = time.time() - start_time
        return Response({
            "data": cached_product,
            "cached": True,
            "response_time": f"{duration:.4f} seconds"
        })

    product = Product.objects(slug=slug).first()
    if not product:
        return Response({"error": "Not found"}, status=404)

    serializer = ProductSerializer(product)
    cache.set(cache_key, serializer.data, timeout=300)

    duration = time.time() - start_time
    return Response({
        "data": serializer.data,
        "cached": False,
        "response_time": f"{duration:.4f} seconds"
    })