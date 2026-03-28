from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User
from team_finder.constants import AVATAR_COLORS


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "avatar_preview",
        "email",
        "name",
        "surname",
        "is_staff",
        "is_active",
    )
    list_display_links = ("email",)
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "name", "surname")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Личные данные",
            {
                "fields": (
                    "name",
                    "surname",
                    "avatar",
                    "phone",
                    "github_url",
                    "about",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "name",
                    "surname",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def avatar_preview(self, obj):
        if obj.avatar and obj.avatar.name:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url,
            )
        elif obj.name:
            # Если аватар не загружен, показываем первую букву имени
            color = self._get_avatar_color(obj.id)
            return format_html(
                '<div style="width: 40px; height: 40px; border-radius: 50%; '
                "background-color: {}; display: flex; align-items: center; "
                "justify-content: center; color: white; font-weight: bold; "
                'font-size: 18px;">{}</div>',
                color,
                obj.name[0].upper(),
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; '
            "background-color: #ccc; display: flex; align-items: center; "
            'justify-content: center; color: white; font-weight: bold;">?</div>'
        )

    avatar_preview.short_description = "Аватар"
    avatar_preview.admin_order_field = "avatar"

    def _get_avatar_color(self, user_id):
        return (
            AVATAR_COLORS[user_id % len(AVATAR_COLORS)]
            if user_id
            else AVATAR_COLORS[0]
        )

    def save_model(self, request, obj, form, change):
        if not change and not obj.avatar:
            obj._generate_avatar()
        super().save_model(request, obj, form, change)
