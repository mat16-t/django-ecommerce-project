from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, views as LoginView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.conf import settings
from django.contrib import messages
from .models import CustomUser
import requests

# Google OAuth Login (handles token exchange and login)
def google_login(request):
    """ Handle Google login using token from frontend """
    if request.method == 'POST':
        google_token = request.POST.get('token')  # Token sent from frontend
        if google_token:
            user_info = get_google_user_info(google_token)
            if user_info:
                user = authenticate_or_create_user(user_info)
                login(request, user)
                return JsonResponse({"message": "Login successful", "status": "success", "user": user_info})
            else:
                return JsonResponse({"message": "Google login failed", "status": "error"})
    return JsonResponse({"message": "No token provided", "status": "error"})

def get_google_user_info(google_token):
    """Fetch Google user info using the token."""
    url = f'https://oauth2.googleapis.com/tokeninfo?id_token={google_token}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Returns user data from Google
    return None

def authenticate_or_create_user(user_info):
    """Authenticate or create user based on Google data."""
    try:
        user = User.objects.get(email=user_info['email'])
    except User.DoesNotExist:
        # Create a new user if it doesn't exist
        user = User.objects.create_user(username=user_info['email'], email=user_info['email'], password=None)
        user.first_name = user_info['given_name']
        user.last_name = user_info['family_name']
        user.save()
    return user

# User Registration View
def signup(request):
    """ Register a new user manually """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

# User Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')  # or wherever you want to redirect
        else:
            # Check if username exists
            from .models import CustomUser
            if CustomUser.objects.filter(username=username).exists():
                messages.error(request, 'Incorrect password.')
            else:
                messages.error(request, 'Username does not exist.')
    
    return render(request, 'users/login.html')

# Guest Checkout View
def guest_checkout(request):
    """ Handle guest checkout, collecting user details if not logged in """
    if request.method == 'POST':
        user_details = {
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'shipping_address': request.POST.get('shipping_address')
        }
        
        # Store guest details in session
        request.session['guest_user_details'] = user_details
        return JsonResponse({"message": "Guest checkout details stored. Proceeding to payment."})

    return render(request, 'users/guest_checkout.html')

# User Profile View
@login_required
def profile(request):
    """ User profile page, accessible only if logged in """
    return render(request, 'users/profile.html', {'user': request.user})

# Profile Update View for registered users
# @login_required
# def profile_update(request):
#     """ Update user profile (e.g., address, phone number, etc.) """
#     if request.method == 'POST':
#         request.user.phone_number = request.POST.get('phone_number')
#         request.user.profile_picture = request.FILES.get('profile_picture')
#         request.user.save()
#         return JsonResponse({"message": "Profile updated successfully"})
#     return render(request, 'users/profile_update.html', {'user': request.user})

# Convert guest user to full user
def convert_guest_to_user(request):
    """ If guest proceeds with checkout, convert them to a full user account """
    if 'guest_user_details' in request.session:
        guest_data = request.session['guest_user_details']
        # Create a new user
        user = User.objects.create_user(
            username=guest_data['email'],
            email=guest_data['email'],
            password=None  # No password for guest-created user
        )
        user.first_name = guest_data['name']
        user.save()

        # Log them in
        login(request, user)
        return redirect('profile')
    return redirect('guest_checkout')  # Redirect back to guest checkout if no guest details are found

@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        user.address = request.POST.get('address')
        if 'profile_picture' in request.profile_pictures:
            user.profile_picture = request.profile_picture['profile_picture']
        user.save()
        return redirect('profile')

    return render(request, 'users/profile.html', {'user': user})

@login_required
def delete_profile_info(request):
    user = request.user

    # Optionally clear User fields
    user.is_active = False
    user.first_name = ''
    user.last_name = ''
    user.username = ''
    user.email = ''
    user.save()

    # Clear UserProfile fields
    try:
        user.phone = ''
        user.address = ''
        # Clear other fields...
        user.save()
    except CustomUser.DoesNotExist:
        pass

    return redirect('store:home')