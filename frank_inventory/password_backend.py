from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel.objects.get(**{UserModel.USERNAME_FIELD + '__iexact': username})
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
