# orders/views.py
import razorpay
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem
from store.models import CartItem
from products.models import Product
from .serializers import OrderSerializer
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt

# class OrderViewSet(viewsets.ModelViewSet):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]  # Only authenticated users can access their orders

#     def get_queryset(self):
#         """
#         Optionally restricts the returned orders to the current user,
#         by filtering against a `user` query parameter in the URL.
#         """
#         queryset = Order.objects.all()
#         user = self.request.user
#         if user.is_authenticated:
#             queryset = queryset.filter(user=user)
#         return queryset

@login_required
def place_order(request):
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        return render(request, 'orders/order_error.html', {'message': 'Your cart is empty.'})

    total = 0
    order_items_data = []

    # Step 1: Calculate total and prepare order item data
    for item in cart_items:
        product = Product.objects(product_id=item.product_id).first()
        variant = None

        if not product:
            continue  # skip invalid product

        for v in product.variants:
            if v.variant_id == item.variant_id:
                variant = v
                break

        if not variant:
            continue  # skip invalid variant

        subtotal = variant.price * item.quantity
        total += subtotal

        order_items_data.append({
            'product_id': item.product_id,
            'variant_id': item.variant_id,
            'quantity': item.quantity,
            'price': variant.price
        })

        # Optional: reduce stock in MongoDB
        variant.stock -= item.quantity
        product.save()

    if not order_items_data:
        return render(request, 'orders/order_error.html', {'message': 'No valid items found in cart.'})

    # Step 2: Create Order
    order = Order.objects.create(
        user=request.user,
        total_amount=total,
        status='Pending'
    )

    # Step 3: Create OrderItems
    for item_data in order_items_data:
        OrderItem.objects.create(
            order=order,
            product_id=item_data['product_id'],
            variant_id=item_data['variant_id'],
            quantity=item_data['quantity'],
            price=item_data['price']
        )

    send_mail(
        subject='Order Confirmation',
        message=f'Thank you for your order #{order.id}! Total: ₹{total}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=True
    )

    # Step 4: Clear cart
    cart_items.delete()

    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def order_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_view.html', {
        'orders': orders
    })

def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    items = order.items.all()

    product_data = {}
    for item in items:
        try:
            product = Product.objects.get(product_id=item.product_id)
            product_data[item.product_id] = {
                "name": product.name,
                "price": product.price,
                "specs": product.specs,
                "quantity": item.quantity
            }
        except Product.DoesNotExist:
            product_data[item.product_id] = {
                "name": "Unknown",
                "price": 0,
                "quantity": item.quantity
            }

    return render(request, "orders/order_detail.html", {
        "order": order,
        "items": product_data.values()
    })

def initiate_payment(request, order_id):
    order = Order.objects.get(id=order_id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": int(order.total_amount * 100),  # Amount in paise
        "currency": "INR",
        "payment_capture": 1
    })

    order.razorpay_order_id = razorpay_order['id']
    order.save()

    context = {
        "order": order,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": razorpay_order['id'],
        "amount": order.total_amount,
        "user": request.user
    }
    return render(request, 'orders/payment_page.html', context)


@csrf_exempt
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    order_id = request.GET.get('order_id')
    
    order = Order.objects.get(id=order_id)
    order.payment_id = payment_id
    order.status = 'Paid'
    order.save()
    
    return render(request, 'orders/payment_success.html', {'order': order})