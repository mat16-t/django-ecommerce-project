# store/views.py

from django.shortcuts import render, get_object_or_404, redirect
from products.models import Product, Category, ProductVariant
from products.filters import filter_products
from django.http import JsonResponse
from .models import CartItem 
import re, json
from bson import ObjectId
from orders.models import Order, OrderItem
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import cache_page
from mongoengine.errors import NotUniqueError
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .typesense_client import typesense_client
from .typesense_sync import index_product

def home(request):
    avatar_url = None
    categories = Category.objects.all()
    if request.user.is_authenticated:
        try:
            social_account = SocialAccount.objects.get(user=request.user)
            avatar_url = social_account.get_avatar_url()  # Get avatar URL
        except SocialAccount.DoesNotExist:
            avatar_url = None
    
    return render(request, 'store/home.html', {'avatar_url': avatar_url, 'categories': categories})

# Home / Product listing
@cache_page(60*15)
def product_list(request):
    filtered_products = filter_products(request.GET)
    categories = Product.objects().distinct('category')
    brands = Product.objects().distinct('brand')

    # Variants are inside embedded documents
    storages = set()
    colors = set()

    for product in Product.objects():
        for variant in product.variants:
            storages.add(variant.storage)
            colors.add(variant.color)
    context = {
        'products': filtered_products,
        'categories': categories,
        'brands': brands,
        'storages': sorted(storages),
        'colors': sorted(colors),
    }
    # products = Product.objects.all()
    return render(request, 'store/product_list.html', context)

# Filter by category
def category_products(request, slug):
    cache_key = f"category_products_{slug.lower()}"
    products = cache.get(cache_key)

    if products is None:
        # Fetch from MongoDB using MongoEngine
        products = Product.objects(category__regex=re.compile(f'^{slug}$', re.IGNORECASE))
        cache.set(cache_key, products, timeout=900)  # Cache for 15 minutes

    return render(request, 'store/category_products.html', {
        'category': slug.capitalize(),
        'products': products
    })

# Product detail page
def product_detail(request, slug):
    product = Product.objects(slug=slug).first()
    slug=slug
    if not product:
        return redirect('store:product-list')  # fallback if product not found

    selected_variant = None

    if request.method == 'POST':
        variant_index = int(request.POST.get('variant_index', 0))
        try:
            selected_variant = product.variants[variant_index]
        except IndexError:
            selected_variant = product.variants[0] if product.variants else None
    else:
        selected_variant = product.variants[0] if product.variants else None

    context = {
        'product': product,
        'selected_variant': selected_variant,
        'selected_index': product.variants.index(selected_variant) if selected_variant else 0,
        'slug': slug
    }

    return render(request, 'store/product_detail.html', context)

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'store/signup.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        variant_id = request.POST.get('variant_id')
        user = request.user

        product = Product.objects(variants__variant_id=variant_id).first()
        product_id = product.product_id if product else "UNKNOWN"
        if not product:
            messages.error(request, "Product not found.")
            return redirect('store:product-list')

        # Find the selected variant
        variant = next((v for v in product.variants if v.variant_id == variant_id), None)

        if not variant:
            messages.error(request, "Variant not found.")
            return redirect('store:product-detail', product_id=product_id)

        if variant.stock <= 0:
            messages.warning(request, f"Variant '{variant_id}' is out of stock.")
            return redirect('store:product-detail', product_id=product_id)

        # Get or create CartItem (using product_id + variant_id to ensure uniqueness)
        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product_id=product_id,
            variant_id=variant_id,
        )

        if not created:
            if variant.stock < cart_item.quantity + 1:
                messages.warning(request, f"Only {variant.stock} left in stock.")
                return redirect('store:view-cart')

            cart_item.quantity += 1
        else:
            cart_item.quantity = 1

        cart_item.save()

        # Decrease stock
        variant.stock -= 1
        product.save()

        messages.success(request, f"Added {product.name} - {variant_id} to cart.")
        return redirect('store:view-cart')

    return redirect('store:home')

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    print(cart_items)
    enriched_items = []
    total = 0

    for item in cart_items:
        # Get product from MongoDB
        product = Product.objects(product_id=item.product_id).first()
        variant = None

        if product:
            # Find variant by variant_id
            for v in product.variants:
                if v.variant_id == item.variant_id:
                    variant = v
                    break

        if product and variant:
            subtotal = variant.price * item.quantity
            total += subtotal

            enriched_items.append({
                'product_name': product.name,
                'product_id': product.product_id,
                'price': variant.price,
                'quantity': item.quantity,
                'subtotal': subtotal,
                'image_url': variant.image_url,
            })

    return render(request, 'store/cart.html', {
        'cart_items': enriched_items,
        'total': total
    })


@login_required
def update_cart_quantity(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        user = request.user

        try:
            cart_item = CartItem.objects.get(user=user, product_id=product_id)
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Item not found in cart.'}, status=404)

        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        cart_item.save()

        # Recalculate totals
        all_cart_items = CartItem.objects.filter(user=user)
        total = sum(item.subtotal() for item in all_cart_items)

        return JsonResponse({
            'quantity': cart_item.quantity,
            'subtotal': f'{cart_item.subtotal():.2f}',
            'total': f'{total:.2f}'
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def place_order(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=request.user)
    total = 0
    order = Order.objects.create(user=request.user)

    for item in cart_items:
        product = item.get_product()
        if product:
            subtotal = product.price * item.quantity
            total += subtotal

            OrderItem.objects.create(
                order=order,
                product_id=str(product.id),
                quantity=item.quantity,
                price=product.price
            )

    order.total_amount = total
    order.save()

    # Send email
    send_mail(
        subject='Order Confirmation',
        message=f'Thank you for your order #{order.id}! Total: ₹{total}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True
    )

    # Clear cart
    cart_items.delete()

    return redirect('orders:order-success')

@staff_member_required
@csrf_exempt
def add_or_update_product(request):
    if request.method == 'GET':
        return render(request, 'store/add_product.html')
    # for product in Product.objects:
    #     index_product(product)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            product_id = data.get('product_id')
            variants_data = data.get('variants', [])

            # Check if the product already exists
            existing_product = Product.objects.filter(product_id=product_id).first()
            if existing_product:
                # Only update with new unique variants
                for v in variants_data:
                    if not any(existing_v.variant_id == v['variant_id'] for existing_v in existing_product.variants):
                        existing_product.variants.append(ProductVariant(**v))
                existing_product.save()
                return JsonResponse({'message': 'Product updated with new variants'})
            
            else:
                # Create new product
                product = Product(
                    product_id=product_id,
                    name=data.get('name'),
                    description=data.get('description'),
                    category=data.get('category'),
                    brand=data.get('brand'),
                    # image_url=data.get('image_url'),
                    specifications=data.get('specifications', {})
                )
                product.variants = [ProductVariant(**v) for v in variants_data]
                product.save()
                index_product(product)
                messages.success(request, 'Product added successfully.')
                return redirect('add-product')

        except NotUniqueError:
            return redirect('add-product')
        except json.JSONDecodeError:
            messages.error(request, 'Duplicate product or variant ID.')
            return redirect('add-product')
        except Exception as e:
            return redirect('add-product')

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def search_products(request):
    query = request.GET.get('q', '')
    if not query:
        return Response({"error": "Missing query string"}, status=400)

    try:
        search_results = typesense_client.collections['products'].documents.search({
            'q': query,
            'query_by': 'name,description,brand,category,color,storage',
            'sort_by': 'price:asc',
            'per_page': 20,
        })
        return Response(search_results['hits'])
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
def product_search_view(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'store/search_results.html', {'query': '', 'results': [], 'error': 'Missing query'})
    try:
        search_results = typesense_client.collections['products'].documents.search({
            'q': query,
            'query_by': 'name,description,brand,category,color,storage',
            'sort_by': 'price:asc',
            'per_page': 20,
        })
        # return Response(search_results['hits'])
        return render(request, 'store/search_results.html', {'query': query, 'results': search_results['hits']})
    except Exception as e:
        return render(request, 'store/search_results.html', {'query': query, 'results': [], 'error': str(e)})
    
def suggest_view(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({"suggestions": []})

    try:
        result = typesense_client.collections['products'].documents.search({
            'q': query,
            'query_by': 'name,brand',
            # 'autocomplete': 'true',
            'prefix': 'true',
            'per_page': 5,
        })

        suggestions = [hit['document']['name'] for hit in result.get('hits', [])]
        return JsonResponse({"suggestions": suggestions})
    except Exception as e:
        return JsonResponse({"suggestions": [],"error": str(e)}, status=500)

def add_to_compare(request):
    product_id = request.POST.get('product_id')
    print(product_id)
    
    if not product_id:
        messages.error(request, "Invalid product ID.")
        return redirect('store:home')  # or any fallback
    compare_list = request.session.get('compare_list', [])

    if product_id not in compare_list:
        compare_list.append(product_id)
        request.session['compare_list'] = compare_list

    return redirect('store:compare-view')

def compare_view(request):
    compare_list = request.session.get('compare_list')
    products = Product.objects.filter(product_id__in=compare_list)
    return render(request, 'store/compare.html', {'products': products})

def remove_from_compare(request, product_id):
    if request.method == 'POST':
        print(product_id)
        compare_list = request.session.get('compare_list', [])

        if product_id in compare_list:
            compare_list.remove(str(product_id))
            messages.success(request, "Item removed from comparison.")
        else:
            messages.error(request, "Item not found in comparison list.")

        # Update the session
        request.session['compare_list'] = compare_list
    return redirect('store:compare-view')
