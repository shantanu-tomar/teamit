from django.shortcuts import render
from .models import Portal
from projects.models import Member
from django.conf import settings
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from .extras import CustomPasswordResetForm
from django.views.generic.base import TemplateView

from .serializers import (
    UserSerializer, ProfileUserSerializer,
    LoginSerializer, PortalSerializer
)
from rest_framework import generics, viewsets
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status, permissions
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
# from rest_framework.parsers import FileUploadParser
from django.contrib.auth.views import PasswordContextMixin
from django.contrib.auth import update_session_auth_hash

from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from django.core.exceptions import (
    FieldDoesNotExist, ImproperlyConfigured, ValidationError,
)
from django.contrib.auth.password_validation import get_default_password_validators
from rest_framework import serializers
from .de_en_crypt_password import decrypt
from rest_auth.registration.views import RegisterView
from rest_auth.views import LoginView as RestAuthLoginView
from allauth.account import app_settings as allauth_settings
from django.views.decorators.debug import sensitive_post_parameters
from rest_auth.models import TokenModel
from rest_auth.app_settings import (TokenSerializer,
                                    JWTSerializer,
                                    create_token)
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
import operator
from functools import reduce



DECRYPT_PASS = settings.PASS_DECRYPT_KEY
sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password1', 'password2', 'password',
        'old_password', 'new_password1', 'new_password2')
)


def get_user_portals(user):
    # Portals that the user owns or is a member of
    member_qs = Member.objects.filter(user=user)
    member_condition = reduce(operator.or_, [
                         Q(member__id=member.id) for member in member_qs])
        
    user_portals = Portal.objects.filter(
        Q(owner=user) | member_condition).distinct()
    return user_portals



# API VIEWS
class UserCreate(RegisterView, APIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = UserSerializer
    token_model = TokenModel

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(UserCreate, self).dispatch(*args, **kwargs)

    def get_response_data(self, user):
        if allauth_settings.EMAIL_VERIFICATION == \
                allauth_settings.EmailVerificationMethod.MANDATORY:
            return {"detail": _("Verification e-mail sent.")}

        minimal_user_serializer = ProfileUserSerializer(user)
        
        return {
                "token": TokenSerializer(user.auth_token).data,
                "user": minimal_user_serializer.data,
                }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        # headers = self.get_success_headers(serializer.data)

        return Response(self.get_response_data(user),
                        status=status.HTTP_201_CREATED,
                        )

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        create_token(self.token_model, user, serializer)
        return user


class LoginView(RestAuthLoginView):
    permission_classes = ()
    serializer_class = LoginSerializer
    token_model = TokenModel

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def login(self):
        self.user = self.serializer.validated_data['user']

        self.token = create_token(self.token_model, self.user,
                                  self.serializer)

    def get_response(self):
        serializer_class = self.get_response_serializer()

        serializer = serializer_class(instance=self.token,
                                      context={'request': self.request})
        token = serializer.data.get("key")

        user = self.user
        user_serializer = ProfileUserSerializer(user)

        user_portals = get_user_portals(user)
        portal_serializer = PortalSerializer(user_portals, many=True)
    
        response = Response({
            "token": token,
            "portals": portal_serializer.data,
            "user": user_serializer.data,
            },
            status=status.HTTP_200_OK)

        return response

    # @method_decorator(ensure_csrf_cookie)
    def post(self, request, *args, **kwargs):
        self.request = request
        email = request.data.get('email')

        http_origin = request.META.get("HTTP_ORIGIN")
        if http_origin in settings.CLIENT_DOMAINS:
            encrypted_pass = request.data.get('password')
            password = decrypt(encrypted_pass, DECRYPT_PASS.encode()).decode()
        else:
            password = request.data.get('password')

        data = {
         "email": email,
         "password": password,
        }
    
        self.serializer = self.get_serializer(data=data,
                                              context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()


class PasswordResetCompleteView(PasswordContextMixin, TemplateView):
    title = ('Password reset complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['login_url'] = settings.LOGIN_URL
        return context


class GetPortalsView(APIView):
    def get(self, request):
        user = request.user

        if not user.is_anonymous:
            user_portals = get_user_portals(user)
            portal_serializer = PortalSerializer(user_portals, many=True)
    
            return Response(portal_serializer.data, status=status.HTTP_200_OK)