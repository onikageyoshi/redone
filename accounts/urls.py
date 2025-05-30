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
from .views import logout_view
from .views import profile_page
from . import views



urlpatterns = [
    path('auth/', AuthView.as_view(), name='auth'),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path('login/', LoginView.as_view(), name='login-user'),
    path("signup/", SignupView.as_view(), name="signup-user"),
    path('logout/', logout_view, name='logout'),
    path('profile/page/', profile_page, name='profile-page'),
]




if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

