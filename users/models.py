import random
import uuid
from io import BytesIO

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont


from users.managers import UserManager
from team_finder.constants import (
    AVATAR_COLORS,
    USER_NAME_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
    ABOUT_TEXTFIELD_MAX_LENGTH,
    AVATAR_IMAGE_SIZE,
    AVATAR_FONT_SIZE,
    AVATAR_IMAGE_FORMAT,
    AVATAR_TEXT_COLOR,
    TEXT_START_X,
    TEXT_START_Y,
    PHONE_NUMBER_LENGTH,
)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    # phone: null=True чтобы несколько пустых значений не конфликтовали по unique
    phone = models.CharField(
        max_length=PHONE_NUMBER_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )
    github_url = models.URLField(blank=True)
    about = models.TextField(
        max_length=ABOUT_TEXTFIELD_MAX_LENGTH, blank=True
    )
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
        color = random.choice(AVATAR_COLORS)
        letter = (self.name[0] if self.name else "?").upper()

        size = AVATAR_IMAGE_SIZE
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
                font = ImageFont.truetype(path, AVATAR_FONT_SIZE)
                break
            except (IOError, OSError):
                continue
        if font is None:
            font = ImageFont.load_default()

        bbox = draw.textbbox(
            (TEXT_START_X, TEXT_START_Y), letter, font=font
        )
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) / 2 - bbox[0]
        y = (size - text_h) / 2 - bbox[1]
        draw.text((x, y), letter, fill=AVATAR_TEXT_COLOR, font=font)

        buf = BytesIO()
        img.save(buf, format=AVATAR_IMAGE_FORMAT)
        buf.seek(0)

        self.avatar.save(
            f"avatar_{uuid.uuid4()}.{AVATAR_IMAGE_FORMAT.lower()}",
            ContentFile(buf.read()),
            save=False,
        )
