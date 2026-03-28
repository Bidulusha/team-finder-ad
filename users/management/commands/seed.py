"""
python manage.py seed

Создаёт тестовые данные: суперпользователя, нескольких пользователей,
навыки и проекты. Безопасен для повторного запуска (использует get_or_create).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User
from team_finder.constants import (
    SUPERUSER_EMAIL,
    SUPERUSER_NAME,
    SUPERUSER_SURNAME,
    SUPERUSER_PASSWORD,
)

import json


class Command(BaseCommand):
    help = "Seed database with test users, projects and skills"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._create_superuser()
            users = self._create_users()
            skills = self._create_skills()
            self._create_projects(users, skills)
        self.stdout.write(
            self.style.SUCCESS("Seed completed successfully.")
        )

    # ── Superuser ──────────────────────────────────────────────────────────────

    def _create_superuser(self):
        if not User.objects.filter(email=SUPERUSER_EMAIL).exists():
            User.objects.create_superuser(
                email=SUPERUSER_EMAIL,
                name=SUPERUSER_NAME,
                surname=SUPERUSER_SURNAME,
                password=SUPERUSER_PASSWORD,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Created superuser: {SUPERUSER_EMAIL} / {SUPERUSER_PASSWORD}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"  Superuser {SUPERUSER_EMAIL} already exists, skipping."
                )
            )

    # ── Users ──────────────────────────────────────────────────────────────────

    def _create_users(self):
        specs = []
        with open("specs.json", "r", encoding="utf-8") as json_file:
            specs = json.load(json_file)

        created = []
        for spec in specs:
            if not User.objects.filter(email=spec["email"]).exists():
                u = User.objects.create_user(
                    email=spec.pop("email"),
                    password=spec.pop("password"),
                    **{k: v for k, v in spec.items()},
                )
                self.stdout.write(f"  Created user: {u.email}")
            else:
                u = User.objects.get(email=spec["email"])
                self.stdout.write(f"  User already exists: {u.email}")
            created.append(u)
        return created

    # ── Skills ─────────────────────────────────────────────────────────────────

    def _create_skills(self):
        names = [
            "Python",
            "Django",
            "FastAPI",
            "JavaScript",
            "TypeScript",
            "React",
            "Vue.js",
            "PostgreSQL",
            "Docker",
            "Kubernetes",
            "Go",
            "Rust",
            "Redis",
            "Figma",
            "CI/CD",
        ]
        skills = []
        for name in names:
            skill, created = Skill.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"  Created skill: {name}")
            skills.append(skill)
        return skills

    # ── Projects ───────────────────────────────────────────────────────────────

    def _create_projects(self, users, skills):
        maria, alex, kate, dmitry = users

        projects_data = []
        with open(
            "projects_data.json", "r", encoding="utf-8"
        ) as json_file:
            projects_data = json.load(json_file)

        for data in projects_data:
            skill_names = data.pop("skill_names")
            participants = data.pop("participant_users")

            project, created = Project.objects.get_or_create(
                name=data["name"],
                owner=data["owner"],
                defaults={
                    k: v
                    for k, v in data.items()
                    if k not in ("name", "owner")
                },
            )
            if created:
                for name in skill_names:
                    skill = Skill.objects.get(name=name)
                    project.skills.add(skill)
                for user in participants:
                    project.participants.add(user)
                self.stdout.write(
                    f"  Created project: {project.name}"
                )
            else:
                self.stdout.write(
                    f"  Project already exists: {project.name}"
                )
