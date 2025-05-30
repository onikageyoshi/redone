from rest_framework import serializers
from .models import LoginLog, SignupLog
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)  
    last_name = serializers.CharField(required=True)   

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name']  

    def create(self, validated_data):
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name")  
        last_name = validated_data.get("last_name")  

        user = User.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)  
        SignupLog.objects.create(user=user, first_name=first_name, last_name=last_name)   

        return user







class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):  
        email = attrs.get("email")  
        password = attrs.get("password")  

        if not email or not password:
            raise serializers.ValidationError({"non_field_errors": ["Both email and password are required."]})

        user = authenticate(username=email, password=password)  
        if user is None:
            raise serializers.ValidationError({"non_field_errors": ["Invalid Email or Password."]})

        attrs["user"] = user  
        return attrs  

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = '__all__'


from rest_framework import serializers
from .models import Profile

