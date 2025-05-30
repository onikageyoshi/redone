from django.contrib import admin

from django.contrib import admin
from .models import SignupLog, LoginLog
from django.contrib import admin
from .models import Profile

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'last_login')

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    def last_login(self, obj):
        return obj.user.last_login

    # Optional: Add search/filter capabilities
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

admin.site.register(Profile, ProfileAdmin)

@admin.register(SignupLog)
class SignupLogAdmin(admin.ModelAdmin):
    list_display = ("user", "users_id", "signup_time")  # Fields shown in the admin list view
 # Enable search by username and UUID
    readonly_fields = ("signup_time",)  # Prevent editing signup time

@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time")
    readonly_fields = ("login_time",)  # Make login_time read-only
