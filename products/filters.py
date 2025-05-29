from .models import Product
from mongoengine.queryset.visitor import Q

def filter_products(query_params):
    query = Q()

    # Filter top-level fields directly in MongoDB
    if 'category' in query_params and query_params['category']:
        query &= Q(category=query_params['category'])

    if 'brand' in query_params and query_params['brand']:
        query &= Q(brand=query_params['brand'])

    # Get all matching products first (top-level filters)
    products = Product.objects(query)
    # Extract variant-level filters
    color = query_params.get('color')
    storage = query_params.get('storage')
    min_price = query_params.get('min_price')
    max_price = query_params.get('max_price')

    sort_by = query_params.get('sort_by', '')
    
    # Convert price range safely
    try:
        min_price = float(min_price) if min_price else 0
    except ValueError:
        min_price = 0
    try:
        max_price = float(max_price) if max_price else float('inf')
    except ValueError:
        max_price = float('inf')


    if sort_by == 'price_asc':
        products = products.order_by('variants__price')
    elif sort_by == 'price_desc':
        products = products.order_by('-variants__price')

    # Manual filtering on embedded variant fields
    def variant_matches(variant):
        if color and variant.color != color:
            return False
        if storage and variant.storage != storage:
            return False
        if not min_price <= variant.price <= max_price:
            return False
        return True

    filtered_products = []

    for product in products:
        # If any variant matches the filters, include the product
        matching_variants = [v for v in product.variants if variant_matches(v)]
        if matching_variants:
            if sort_by == 'price_asc':
                matching_variants.sort(key=lambda x: x.price)
            elif sort_by == 'price_desc':
                matching_variants.sort(key=lambda x: -x.price)
            # Optionally, you can attach only matching variants to the product
            product.variants = matching_variants
            filtered_products.append(product)

    if sort_by == 'price_asc':
        filtered_products.sort(key=lambda p: p.variants[0].price if p.variants else float('inf'))
    elif sort_by == 'price_desc':
        filtered_products.sort(key=lambda p: -(p.variants[0].price) if p.variants else float('-inf'))

    return filtered_products
