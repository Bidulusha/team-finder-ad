"""
python manage.py seed

Создаёт тестовые данные: суперпользователя, нескольких пользователей,
навыки и проекты. Безопасен для повторного запуска (использует get_or_create).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project, Skill
from users.models import User


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
        if not User.objects.filter(
            email="admin@teamfinder.ru"
        ).exists():
            User.objects.create_superuser(
                email="admin@teamfinder.ru",
                name="Admin",
                surname="Adminov",
                password="adminpass123",
            )
            self.stdout.write(
                "  Created superuser: admin@teamfinder.ru / adminpass123"
            )
        else:
            self.stdout.write("  Superuser already exists, skipping.")

    # ── Users ──────────────────────────────────────────────────────────────────

    def _create_users(self):
        specs = [
            dict(
                email="maria@yandex.ru",
                name="Мария",
                surname="Иванова",
                password="password",
                about="Фронтенд-разработчик, люблю React и TypeScript.",
                github_url="https://github.com/maria",
            ),
            dict(
                email="alex@example.com",
                name="Алексей",
                surname="Петров",
                password="password",
                about="Python-бэкендер, фанат Django и FastAPI.",
                github_url="https://github.com/alex",
            ),
            dict(
                email="kate@example.com",
                name="Катерина",
                surname="Смирнова",
                password="password",
                about="UX/UI дизайнер, работаю в Figma.",
                github_url="",
            ),
            dict(
                email="dmitry@example.com",
                name="Дмитрий",
                surname="Козлов",
                password="password",
                about="DevOps, Kubernetes, CI/CD enthusiast.",
                github_url="https://github.com/dmitry",
            ),
        ]
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

        projects_data = [
            dict(
                name="TeamFinder Clone",
                description="Клон платформы TeamFinder для практики Django. Ищу фронтенд-разработчика и дизайнера.",
                owner=maria,
                status="open",
                github_url="https://github.com/maria/teamfinder-clone",
                skill_names=[
                    "Python",
                    "Django",
                    "React",
                    "PostgreSQL",
                ],
                participant_users=[maria, alex],
            ),
            dict(
                name="Personal Finance Tracker",
                description="Приложение для учёта личных финансов. Стек: FastAPI + Vue.js + PostgreSQL.",
                owner=alex,
                status="open",
                github_url="https://github.com/alex/finance-tracker",
                skill_names=[
                    "Python",
                    "FastAPI",
                    "Vue.js",
                    "PostgreSQL",
                    "Docker",
                ],
                participant_users=[alex, kate],
            ),
            dict(
                name="Open Source Design System",
                description="Дизайн-система с открытым исходным кодом. Компоненты React, документация в Storybook.",
                owner=kate,
                status="open",
                github_url="",
                skill_names=[
                    "Figma",
                    "React",
                    "TypeScript",
                    "JavaScript",
                ],
                participant_users=[kate, maria],
            ),
            dict(
                name="K8s Monitoring Dashboard",
                description="Дашборд для мониторинга кластеров Kubernetes. Бэкенд на Go, фронт на React.",
                owner=dmitry,
                status="open",
                github_url="https://github.com/dmitry/k8s-dashboard",
                skill_names=[
                    "Go",
                    "Kubernetes",
                    "React",
                    "Docker",
                    "CI/CD",
                ],
                participant_users=[dmitry, alex],
            ),
            dict(
                name="URL Shortener",
                description="Сервис сокращения ссылок с аналитикой переходов. Завершённый учебный проект.",
                owner=alex,
                status="closed",
                github_url="https://github.com/alex/url-shortener",
                skill_names=["Python", "FastAPI", "Redis"],
                participant_users=[alex],
            ),
        ]

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
