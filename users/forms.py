from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import Account


class RegisterForm(UserCreationForm):

    email = forms.EmailField(max_length=255)

    class Meta:
        model = Account
        fields = ('email', 'username', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            Account.objects.get(email=email)
        except Account.DoesNotExist:
            return email

        raise forms.ValidationError('User with this email already exists')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            Account.objects.get(username=username)
        except Account.DoesNotExist:
            return username

        raise forms.ValidationError('User with this username already exists')


class LoginForm(forms.Form):

    email = forms.EmailField(widget=forms.EmailInput)
    password = forms.CharField(label='password', widget=forms.PasswordInput)

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data.get('email')
            password = self.cleaned_data.get('password')

            if not authenticate(email=email, password=password):
                raise forms.ValidationError('Invalid credentials')

