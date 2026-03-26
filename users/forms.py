import re

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import User


class RegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=124,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": "Имя"}),
    )
    surname = forms.CharField(
        max_length=124,
        label="Фамилия",
        widget=forms.TextInput(attrs={"placeholder": "Фамилия"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"placeholder": "example@mail.ru"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "Пользователь с таким email уже существует."
            )
        return email


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"placeholder": "example@mail.ru"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль"}),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self._user = None

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email", "").lower()
        password = cleaned.get("password", "")
        if email and password:
            user = authenticate(
                self.request, username=email, password=password
            )
            if user is None:
                raise ValidationError("Неверный имейл или пароль")
            self._user = user
        return cleaned

    def get_user(self):
        return self._user


def _normalize_phone(phone: str) -> str:
    """Приводит номер к формату +7XXXXXXXXXX."""
    phone = phone.strip()
    if phone.startswith("8"):
        return "+7" + phone[1:]
    return phone


def _validate_phone(phone: str, current_user_id=None) -> str:
    """Валидирует и нормализует телефонный номер."""
    if not phone:
        return phone
    phone = phone.strip()
    if not re.fullmatch(r"(8\d{10}|\+7\d{10})", phone):
        raise ValidationError(
            "Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )
    normalized = _normalize_phone(phone)
    qs = User.objects.filter(phone=normalized)
    if current_user_id:
        qs = qs.exclude(pk=current_user_id)
    if qs.exists():
        raise ValidationError(
            "Этот номер телефона уже используется другим пользователем."
        )
    return normalized


def _validate_github_url(url: str) -> str:
    if not url:
        return url
    if not re.match(r"https?://(www\.)?github\.com/", url):
        raise ValidationError(
            "Ссылка должна вести на GitHub (https://github.com/...)."
        )
    return url


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "name",
            "surname",
            "avatar",
            "about",
            "phone",
            "github_url",
        ]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "about": forms.Textarea(attrs={"rows": 4}),
            "phone": forms.TextInput(
                attrs={"placeholder": "+7XXXXXXXXXX или 8XXXXXXXXXX"}
            ),
            "github_url": forms.URLInput(
                attrs={"placeholder": "https://github.com/username"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self._current_user_id = kwargs.pop("current_user_id", None)
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required = False
        self.fields["phone"].required = False
        self.fields["github_url"].required = False
        self.fields["about"].required = False

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        return _validate_phone(phone, self._current_user_id)

    def clean_github_url(self):
        return _validate_github_url(
            self.cleaned_data.get("github_url", "")
        )


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(),
    )
    new_password2 = forms.CharField(
        label="Подтвердите новый пароль",
        widget=forms.PasswordInput(),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def clean_old_password(self):
        old = self.cleaned_data["old_password"]
        if self._user and not self._user.check_password(old):
            raise ValidationError("Неверный текущий пароль.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Новые пароли не совпадают.")
        return cleaned
