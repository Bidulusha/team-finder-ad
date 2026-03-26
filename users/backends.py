from django.contrib.auth.backends import ModelBackend

from .models import User


class EmailBackend(ModelBackend):
    """Аутентификация по email вместо username."""

    def authenticate(
        self, request, username=None, password=None, **kwargs
    ):
        # Django передаёт логин через параметр username даже для кастомных полей
        email = (username or "").lower().strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(
            password
        ) and self.user_can_authenticate(user):
            return user
        return None
