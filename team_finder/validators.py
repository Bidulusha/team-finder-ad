import re

from django.core.exceptions import ValidationError
from team_finder.constants import ALLOWED_REPOSITORY_PREFIX
from team_finder.service import normalize_phone

from users.models import User


def validate_github_link(url: str) -> str:
    if not url:
        return url

    if not url.startswith(ALLOWED_REPOSITORY_PREFIX):
        raise ValidationError(
            "Ссылка должна вести на GitHub (https://github.com/...)."
        )
    return url


def validate_phone(phone: str, current_user_id=None) -> str:
    if not phone:
        return phone
    phone = phone.strip()
    if not re.fullmatch(r"(8\d{10}|\+7\d{10})", phone):
        raise ValidationError(
            "Введите номер в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )
    normalized = normalize_phone(phone)
    qs = User.objects.filter(phone=normalized)
    if current_user_id:
        qs = qs.exclude(pk=current_user_id)
    if qs.exists():
        raise ValidationError(
            "Этот номер телефона уже используется другим пользователем."
        )
    return normalized
