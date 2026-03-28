from django.contrib.auth.models import (
    BaseUserManager,
)

class UserManager(BaseUserManager):
    def create_user(
        self, email, name, surname, password=None, **extra_fields
    ):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(
            email=email, name=name, surname=surname, **extra_fields
        )
        user.set_password(password)
        user._generate_avatar()
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, name, surname, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(
            email, name, surname, password, **extra_fields
        )