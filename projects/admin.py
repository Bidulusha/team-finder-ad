from django.contrib import admin

from .models import Project, Skill


# ========== SKILL ADMIN ==========
class SkillModelAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ========== PROJECT ADMIN ==========
class ProjectModelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "owner__email")
    filter_horizontal = ("participants", "skills", "favorites")  #
    readonly_fields = ("created_at",)


# Регистрация моделей
admin.site.register(Skill, SkillModelAdmin)
admin.site.register(Project, ProjectModelAdmin)
