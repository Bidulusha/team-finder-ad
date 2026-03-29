from django.contrib import admin
from django.utils.html import format_html

from projects.models import Project, Skill


# ========== SKILL ADMIN ==========
@admin.register(Skill)
class SkillModelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ========== PROJECT ADMIN ==========
@admin.register(Project)
class ProjectModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "created_at",
        "participants_count",
    )
    list_filter = ("status",)
    search_fields = ("name", "owner__email")
    filter_horizontal = ("participants", "skills", "favorites")
    readonly_fields = ("created_at",)

    @admin.display(
        ordering="participants",
        description="Участники",
    )
    def participants_count(self, obj):
        count = obj.participants.count()
        return format_html(
            '<span style="display: inline-flex; align-items: center; gap: 4px;">'
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" '
            'fill="currentColor"/></svg>'
            "<strong>{}</strong></span>",
            count,
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("participants")
