# typesense_sync.py
from .typesense_client import typesense_client
from uuid import uuid4

def create_or_update_collection():
    schema = {
        "name": "products",
        "fields": [
            {"name": "variant_id", "type": "string"},
            {"name": "product_id", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "brand", "type": "string", "facet": True},
            {"name": "category", "type": "string", "facet": True},
            {"name": "slug", "type": "string"},
            {"name": "price", "type": "float"},
            {"name": "color", "type": "string", "facet": True},
            {"name": "storage", "type": "string", "facet": True},
        ]
    }

    try:
        print("Attempting to create collection...")
        print("Schema:", schema)
        typesense_client.collections.create(schema)
    except Exception as e:
        print("Collection may already exist:", str(e))


def index_product(product):
    for variant in product.variants:
        print(product)
        document = {
                "variant_id": variant.variant_id or str(uuid4()),
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description or "",
                "brand": product.brand or "",
                "category": product.category or "",
                "slug": product.slug or "",
                "price": float(variant.price) if variant.price else 0.0,
                "color": variant.color or "",
                "storage": str(variant.storage) or "",
            }

        try:
            typesense_client.collections['products'].documents.upsert(document)
            print(f"Indexed variant: {variant.variant_id} of product: {product.name}")
        except Exception as e:
            print(f"Failed to index variant {variant.variant_id}:", str(e))
