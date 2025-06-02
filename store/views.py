from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login as django_login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from accounts.serializers import SignupSerializer, LoginSerializer
from accounts.models import Profile
from store.models import Product

from .models import Cart, CartItem, Order, OrderItem, PaymentMethod, DeliveryService
from .serializers import CartSerializer, CartItemSerializer, ProductSerializer, OrderSerializer, PaymentMethodSerializer, DeliveryServiceSerializer

User = get_user_model()

class CheckoutPageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="View checkout page",
        operation_description="Displays the checkout page with cart summary",
        responses={200: "Checkout page rendered"}
    )
    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart:
            return render(request, "checkout.html", {
                "cart_items": [],
                "total": 0,
                "payment_methods": PaymentMethod.objects.all(),
                "delivery_services": DeliveryService.objects.all(),
            })

        cart_items = cart.items.select_related("product").all()
        total = sum(item.total_price for item in cart_items)

        context = {
            "cart_items": cart_items,
            "total": total,
            "payment_methods": PaymentMethod.objects.all(),
            "delivery_services": DeliveryService.objects.all(),
        }
        return render(request, "checkout.html", context)

    @swagger_auto_schema(
        operation_summary="Process checkout",
        operation_description="Creates an order from cart items and clears the cart",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment method name (e.g. cod, paypal)'),
                'delivery_service': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery service name (optional)'),
                'delivery_address': openapi.Schema(type=openapi.TYPE_STRING, description='Delivery address'),
                'delivery_postal_code': openapi.Schema(type=openapi.TYPE_STRING, description='Postal code'),
                'delivery_country': openapi.Schema(type=openapi.TYPE_STRING, description='Country'),
            },
            required=['payment_method', 'delivery_address', 'delivery_postal_code', 'delivery_country']
        ),
        responses={201: "Order created", 400: "Bad Request"}
    )
    def post(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart or not cart.items.exists():
            return Response({"message": "Your cart is empty."}, status=400)

        payment_method_name = request.data.get("payment_method")
        delivery_service_name = request.data.get("delivery_service")
        delivery_address = request.data.get("delivery_address")
        delivery_postal_code = request.data.get("delivery_postal_code")
        delivery_country = request.data.get("delivery_country")

        if not all([payment_method_name, delivery_address, delivery_postal_code, delivery_country]):
            return Response({"message": "All required delivery fields must be provided."}, status=400)

        payment_method = get_object_or_404(PaymentMethod, name=payment_method_name)
        delivery_service = get_object_or_404(DeliveryService, name=delivery_service_name) if delivery_service_name else None

        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            delivery_service=delivery_service,
            delivery_address=delivery_address,
            delivery_postal_code=delivery_postal_code,
            delivery_country=delivery_country,
        )

        for item in cart.items.select_related("product").all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        cart.items.all().delete()

        return Response({
            "message": "Order placed successfully",
            "order_id": order.id
        }, status=201)

        
class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_item_id):
        if not request.user.is_authenticated:
            raise AuthenticationFailed('User is not authenticated')

        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)

        cart_item.delete()

        return Response({
            'message': 'Product removed from cart successfully!',
        }, status=status.HTTP_204_NO_CONTENT)

class UpdateCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_item_id):
        cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
        
        try:
            quantity = int(request.data.get('quantity'))
        except (TypeError, ValueError):
            return Response({"error": "Invalid quantity"}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({"error": "Quantity must be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        return Response({
            'message': 'Cart item updated successfully!',
            'product': {
                'id': cart_item.product.id,
                'name': cart_item.product.name,
                'quantity': cart_item.quantity,
                'total_price': cart_item.total_price,
            }
        }, status=status.HTTP_200_OK)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise Http404("Product not found")

        cart, _ = Cart.objects.get_or_create(user=request.user)

        quantity = int(request.POST.get('quantity', 1))

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return redirect('cart-detail')

class CartView(APIView): 
    def get(self, request):
        cart_items = CartItem.objects.filter(cart__user=request.user)
        total_price = sum(item.total_price for item in cart_items)
        return render(request, 'cart.html', {
            'cart_items': cart_items,
            'total_price': total_price
        })

    def post(self, request):
        if 'remove_item_id' in request.POST:
            item_id = request.POST.get('remove_item_id')
            CartItem.objects.filter(id=item_id, cart__user=request.user).delete()

        elif 'quantity' in request.POST and 'item_id' in request.POST:
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 1))
            try:
                item = CartItem.objects.get(id=item_id, cart__user=request.user)
                item.quantity = quantity
                item.save()
            except CartItem.DoesNotExist:
                pass

        return self.get(request) 

class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, cart_id, format=None):
        try:
            cart = Cart.objects.get(id=cart_id, user=request.user)
        except Cart.DoesNotExist:
            raise Http404("Cart not found")

        product_id = request.data.get("product")
        quantity = request.data.get("quantity", 1)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise Http404("Product not found")

        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)

        return render(request, 'cart.html', {'cart': cart})

    def delete(self, request, cart_id, item_id, format=None):
        try:
            cart = Cart.objects.get(id=cart_id, user=request.user)
        except Cart.DoesNotExist:
            raise Http404("Cart not found")

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            raise Http404("Cart item not found")

        cart_item.delete()

        return render(request, 'cart.html', {'cart': cart})
    
class ProductDetail(APIView):
    @swagger_auto_schema(auto_schema=None)
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        
        related_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]

        return render(request, 'product_detail.html', {
            'product': product,
            'related_products': related_products
        })

@method_decorator(login_required, name='dispatch')
class HomeView(views.APIView):
    def get(self, request):
        return render(request, "home.html", {})

def home(request):
    profile = None
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)

    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', '')

    products = Product.objects.all()

    if search_query:
        products = products.filter(name__icontains=search_query)

    if selected_category:
        products = products.filter(category=selected_category)

    categories = Product.objects.values_list('category', flat=True).distinct()

    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
    })

def category_view(request, category_name):
    products = Product.objects.filter(category=category_name)
    
    categories = sorted({cat[0] for cat in Product.CATEGORY_CHOICES})

    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_name
    })
def product_detail(request, id):
    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        raise Http404("Product not found")
    return render(request, 'product_detail.html', {'product': product})

class SignupView(views.APIView):
    def get(self, request):
        return render(request, 'auth.html')

    @swagger_auto_schema(
        request_body=SignupSerializer,
        responses={
            201: openapi.Response("Signup successful", SignupSerializer),
            400: "Bad request - Invalid data",
        },
        operation_summary="User Signup",
        operation_description="Register a new user with first name, last name, email, and password."
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            django_login(request, user)
            refresh = RefreshToken.for_user(user)

            if request.query_params.get("redirect") == "true":
                return render(request, 'home.html', {
                    "user": user,
                    "message": "Signup successful"
                })

            return Response({
                "message": "Signup successful",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):
    def get(self, request):
        return render(request, 'auth.html')

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Response("Login successful", LoginSerializer),
            400: "Bad request - Invalid credentials",
        },
        operation_summary="User Login",
        operation_description="Authenticate user using email and password, and return access tokens."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            django_login(request, user)
            refresh = RefreshToken.for_user(user)

            if request.query_params.get("redirect") == "true":
                return render(request, 'home.html', {
                    "user": user,
                    "message": "Login successful"
                })

            return Response({
                "message": "Login successful",
                "user_id": user.id,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(login_required, name='dispatch')
class HomeView(views.APIView):
    def get(self, request):
        return render(request, "home.html", {"user": request.user})
    
class ProductListCreateView(views.APIView):
    @swagger_auto_schema(responses={200: ProductSerializer(many=True)})
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ProductSerializer)
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderListCreateView(views.APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: OrderSerializer(many=True)})
    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=OrderSerializer)
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuthView(APIView):
    @swagger_auto_schema(
        operation_summary="Signup or Login and Render auth.html",
        operation_description="""
        Handles both signup and login using JSON data.
        Use ?mode=signup or ?mode=login as query param.
        Renders auth.html with user context after success.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: "Login successful",
            201: "Signup successful",
            400: "Bad request",
        }
    )
    def post(self, request):
        mode = request.query_params.get('mode', 'login').lower()

        if mode == 'signup':
            serializer = SignupSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return render(request, 'auth.html', {
                    "message": "Signup successful",
                    "user": user,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                })
            return render(request, 'auth.html', {
                "errors": serializer.errors,
                "message": "Signup failed"
            })

        elif mode == 'login':
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                login(request, user)
                refresh = RefreshToken.for_user(user)
                return render(request, 'auth.html', {
                    "message": "Login successful",
                    "user": user,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                })
            return render(request, 'auth.html', {
                "errors": serializer.errors,
                "message": "Login failed"
            })

        return Response({"error": "Invalid mode. Use ?mode=signup or ?mode=login"}, status=400)


def logout_view(request):
    logout(request)
    return redirect('auth-page') 
    
class PaymentMethodListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Show payment methods with demo payment platforms and QR code")
    def get(self, request):
        payment_platforms = [
            {"name": "PayPal", "logo_url": "/static/images/paypal.png"},
            {"name": "Stripe", "logo_url": "/static/images/stripe.png"},
            {"name": "Square", "logo_url": "/static/images/square.png"},
            {"name": "Venmo", "logo_url": "/static/images/venmo.png"},
        ]
        account_number = "6986089776"
        homepage_url = request.build_absolute_uri('/')

        return render(request, "payment_methods.html", {
            "payment_platforms": payment_platforms,
            "account_number": account_number,
            "homepage_url": homepage_url,
        })

    @swagger_auto_schema(request_body=PaymentMethodSerializer, operation_summary="Create a new payment method")
    def post(self, request):
        serializer = PaymentMethodSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)