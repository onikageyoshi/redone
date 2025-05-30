from django.urls import path
from .views import ProductListCreateView, OrderListCreateView, HomeView, ProductDetail,  AddToCartView, CartView, CheckoutPageView
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import SignupView, LoginView, AuthView
from . import views
from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from .views import PaymentMethodListCreateView



urlpatterns = [
    path('', views.home, name="homepage"),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('product/<int:pk>/', ProductDetail.as_view(), name='product_detail'),
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('category/<str:category_name>/', views.category_view, name='category'),  # ← this line is key
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path("home/", HomeView.as_view(), name="home"),
    path('cart/', views.CartView.as_view(), name='cart-detail'),
    path('cart/<int:cart_id>/items/', views.CartItemView.as_view(), name='cart-item-list'),
    path('cart/<int:cart_id>/items/<int:item_id>/', views.CartItemView.as_view(), name='cart-item-detail'),
    path('add-to-cart/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('api/cart/', CartView.as_view(), name='cart_api'),  # GET, POST
    path('api/cart/update/', CartView.as_view(), name='update_cart_api'),  # PUT
    path('api/cart/remove/', CartView.as_view(), name='remove_cart_api'), 
    path('update-cart-item/<int:cart_item_id>/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    path('remove-from-cart/<int:cart_item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', CheckoutPageView.as_view(), name='checkout'),
    path('auth/', AuthView.as_view(), name='auth'),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path('login/', LoginView.as_view(), name='login-user'),
    path("signup/", SignupView.as_view(), name="signup-user"),
    path('payment-methods/', PaymentMethodListCreateView.as_view(), name='payment-method-list-create'),
]



if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


