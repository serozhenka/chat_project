from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


Account = get_user_model()


class CaseInsensitiveModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            username = kwargs.get(Account.USERNAME_FIELD)

        try:
            case_insensitive_username_field = f'{Account.USERNAME_FIELD}__iexact'
            user = Account._default_manager.get(**{case_insensitive_username_field: username})
        except Account.DoesNotExist:
            Account.set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
