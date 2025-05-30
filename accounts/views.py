from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect

from .serializers import SignupSerializer, LoginSerializer
from .models import Profile
from .forms import ProfileForm  # if you're using forms
from django.contrib.auth import get_user_model


User = get_user_model()


class SignupView(views.APIView):
    permission_classes = [AllowAny]

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
            Profile.objects.get_or_create(user=user)
            refresh = RefreshToken.for_user(user)

            if request.query_params.get("redirect") == "true":
                return render(request, 'home.html', {"user": user, "message": "Signup successful"})

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
                return render(request, 'home.html', {"user": user, "message": "Login successful"})

            return Response({
                "message": "Login successful",
                "user_id": user.id,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_200_OK)

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
                django_login(request, user)
                Profile.objects.get_or_create(user=user)
                refresh = RefreshToken.for_user(user)
                return render(request, 'auth.html', {
                    "message": "Signup successful",
                    "user": user,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                })
            return render(request, 'auth.html', {"errors": serializer.errors, "message": "Signup failed"})

        elif mode == 'login':
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data["user"]
                django_login(request, user)
                refresh = RefreshToken.for_user(user)
                return render(request, 'auth.html', {
                    "message": "Login successful",
                    "user": user,
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                })
            return render(request, 'auth.html', {"errors": serializer.errors, "message": "Login failed"})

        return Response({"error": "Invalid mode. Use ?mode=signup or ?mode=login"}, status=400)


@login_required
def profile_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()

            # Update first_name and last_name on the User model if changed
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.save()

            return redirect('home')  # Redirect to homepage
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'profiles.html', {
        'profile': profile,
        'form': form,
        'user': request.user
    })

def logout_view(request):
    logout(request)
    return render(request, 'auth.html')
