from django.db import models
from django.conf import settings
from products.models import Product

class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_id = models.CharField(max_length=50, default='TEMP_PRODUCT')
    variant_id = models.CharField(max_length=50, default='TEMP_VARIANT')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'product_id')

    def get_product(self):
        from store.models import Product  # MongoEngine model
        return Product.objects(id=self.product_id).first()

    def __str__(self):
        return f"{self.user} - {self.product_id} - {self.variant_id}"
    
    def subtotal(self):
        from products.models import Product
        product = Product.objects(product_id=self.product_id).first()
        if product and product.variants:
            for variant in product.variants:
                if variant.variant_id == self.variant_id:
                    return variant.price * self.quantity
        return 0.0
