from django import forms
from django.contrib.auth.forms import UserCreationForm
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


