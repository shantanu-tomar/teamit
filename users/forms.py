from django import forms
from django.contrib.auth.forms import UserCreationForm
# from .models import Profile
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
User = get_user_model()


class UserRegisterForm(UserCreationForm):
    name = forms.CharField()
    email = forms.EmailField()

    class Meta:
        model = get_user_model()
        fields = ['name', 'email', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    name = forms.CharField()
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['name', 'email']


# class ProfileUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['image']


# class ResetPasswordForm(PasswordResetForm):
#     username = forms.CharField(max_length=150)