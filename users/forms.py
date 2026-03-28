from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import User
from team_finder.constants import (
    REGISTRATION_FORM_NAME_MAX_LENGTH,
    REGISTRATION_FORM_SURNAME_MAX_LENGTH,
)
from team_finder.validators import (
    validate_github_link,
    validate_phone,
)


class RegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=REGISTRATION_FORM_NAME_MAX_LENGTH,
        label="Имя",
        widget=forms.TextInput(attrs={"placeholder": "Имя"}),
    )
    surname = forms.CharField(
        max_length=REGISTRATION_FORM_SURNAME_MAX_LENGTH,
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
        return validate_phone(phone, self._current_user_id)

    def clean_github_url(self):
        return validate_github_link(
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
        new_password_first_field = cleaned.get("new_password1")
        new_password_second_field = cleaned.get("new_password2")
        if (
            new_password_first_field
            and new_password_second_field
            and new_password_first_field != new_password_second_field
        ):
            raise ValidationError("Новые пароли не совпадают.")
        return cleaned
