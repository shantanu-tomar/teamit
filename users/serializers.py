from .models import Portal

from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_auth.registration.serializers import RegisterSerializer
from rest_auth.serializers import LoginSerializer as RestAuthLoginSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class PortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portal
        fields = '__all__'


class MinimalPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portal
        fields = ('name', )


class UserSerializer(RegisterSerializer):
    username = None
    name = serializers.CharField(max_length=20, required=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_name(self, name):
        return name
    
    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'name': self.validated_data.get('name', ''),
        }


class LoginSerializer(RestAuthLoginSerializer):
    username = None


class ProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'image', 'is_active',
                  'is_staff', 'is_superuser')


# class ProfileSerializer(serializers.ModelSerializer):
#     user = ProfileUserSerializer()
#     wishlist = ProductSerializer(many=True)
#     price_tracking = ProductSerializer(many=True)

#     class Meta:
#         model = Profile
#         fields = '__all__'


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('image', )


# class AboutUsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AboutUs
#         fields = '__all__'