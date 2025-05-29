# users/urls.py
from django.urls import path, include
from . import views
# from django.contrib.auth import views as auth_views  # Import logout view

app_name = 'users'

urlpatterns = [
    # path('google-login/', views.google_login, name='google_login'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='user_login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    # path('profile/update/', views.profile_update, name='profile_update'),
    path('guest-checkout/', views.guest_checkout, name='guest_checkout'),
    path('convert-guest-to-user/', views.convert_guest_to_user, name='convert_guest_to_user'),
    path('delete-account/', views.delete_profile_info, name="delete-profile")
]
