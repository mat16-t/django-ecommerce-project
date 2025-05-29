from django.core.management.base import BaseCommand
from store.models import Product
from store.typesense_client import typesense_client

class Command(BaseCommand):
    help = 'Indexes all products into Typesense'

    def handle(self, *args, **kwargs):
        products = Product.objects()
        count = 0
        for product in products:
            document = {
                "variant_id": product.variants[0].variant_id,
                "product_id": product.product_id,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "category": product.category,
                "slug": product.slug,
                "price": product.variants[0].price if product.variants else 0.0,
                "color": product.variants[0].color if product.variants else "",
                "storage": str(product.variants[0].storage) if product.variants else "",
            }
            try:
                typesense_client.collections['products'].documents.upsert(document)
                self.stdout.write(self.style.SUCCESS(f"Indexed product: {product.name}"))
                count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to index product {product.name}: {str(e)}"))
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} products successfully!"))
