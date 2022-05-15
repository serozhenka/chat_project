from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


def get_profile_image_path(instance, filename):
    # custom account image filepath generator by
    # given instance (account object) and client's
    # image filename

    return f'profile_images/{str(instance.id)}_{filename}'

class AccountManager(BaseUserManager):
    # custom user model manager

    def create_user(self, email, username, password=None, **kwargs):
        if not email:
            raise ValueError('User should have valid email address')
        if not username:
            raise ValueError('User should have valid username')

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            username=username,
            **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, **kwargs):
        user = self.create_user(email, username, password, **kwargs)

        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    # Custom user model with email as username field

    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=50, unique=True)
    joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=get_profile_image_path, default='profile_images/logo_1080_1080.png', null=True, blank=True)
    hide_email = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = AccountManager()

    def __str__(self):
        return self.username

