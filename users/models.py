import random
import uuid
from io import BytesIO

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

# Мягкие, хорошо читаемые цвета фона для аватарок
_AVATAR_COLORS = [
    "#4A90D9",
    "#7B68EE",
    "#48C78E",
    "#F4A261",
    "#2A9D8F",
    "#E9C46A",
    "#8338EC",
    "#3A86FF",
    "#E76F51",
    "#06D6A0",
]


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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    # phone: null=True чтобы несколько пустых значений не конфликтовали по unique
    phone = models.CharField(
        max_length=12, blank=True, null=True, unique=True
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    def _generate_avatar(self):
        """Генерирует аватарку: первая буква имени на цветном фоне."""
        color = random.choice(_AVATAR_COLORS)
        letter = (self.name[0] if self.name else "?").upper()

        size = 200
        img = Image.new("RGB", (size, size), color=color)
        draw = ImageDraw.Draw(img)

        # Пробуем системный шрифт, иначе — дефолтный PIL
        font = None
        for path in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ):
            try:
                font = ImageFont.truetype(path, 100)
                break
            except (IOError, OSError):
                continue
        if font is None:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) / 2 - bbox[0]
        y = (size - text_h) / 2 - bbox[1]
        draw.text((x, y), letter, fill="white", font=font)

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        self.avatar.save(
            f"avatar_{uuid.uuid4()}.png",
            ContentFile(buf.read()),
            save=False,
        )
