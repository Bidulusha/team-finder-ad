from django.conf import settings
from django.db import models
from django.shortcuts import redirect
from team_finder.constants import (
    STATUS_CHOICES,
    SKILL_NAME_MAX_LENGTH,
    PROJECT_NAME_MAX_LENGTH,
)


# ========== SKILL MODEL ==========
class Skill(models.Model):
    name = models.CharField(
        max_length=SKILL_NAME_MAX_LENGTH, unique=True
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ========== PROJECT MODEL ==========
class Project(models.Model):
    name = models.CharField(max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=max(
            [
                max([len(status) for status in status_option])
                for status_option in STATUS_CHOICES
            ]
        ),
        choices=STATUS_CHOICES,
        default="open",
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        related_name="projects",
        blank=True,
    )
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="favorited_projects",
        blank=True,
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return redirect("projects:detail", project_id=self.pk)
