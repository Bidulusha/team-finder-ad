import json
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from team_finder.constants import STATUS_OPEN, MAX_SKIN_IN_PAGE
from projects.models import Project, Skill
from users.models import User


def create_user(
    email="u@example.com",
    name="Test",
    surname="User",
    password="pass1234",
):
    return User.objects.create_user(
        email=email, name=name, surname=surname, password=password
    )


def create_project(owner, name="Test Project", status=STATUS_OPEN):
    project = Project.objects.create(
        name=name, owner=owner, status=status
    )
    project.participants.add(owner)
    return project


class TestDataMixin:
    @classmethod
    def setUpTestData(cls):
        cls.user = create_user()
        cls.owner = create_user(
            email="owner@x.com", name="Owner", surname="One"
        )
        cls.other = create_user(
            email="other@x.com", name="Other", surname="Two"
        )

        cls.project = create_project(cls.owner)

        # URL names from your urls.py
        cls.list_url = reverse("projects:list")
        cls.create_url = reverse("projects:create")
        cls.detail_url = reverse(
            "projects:detail", kwargs={"project_id": cls.project.pk}
        )
        cls.toggle_url = reverse(
            "projects:toggle_participate",
            kwargs={"project_id": cls.project.pk},
        )
        cls.complete_url = reverse(
            "projects:complete", kwargs={"project_id": cls.project.pk}
        )
        cls.favorite_url = reverse(
            "projects:toggle_favorite",
            kwargs={"project_id": cls.project.pk},
        )
        cls.skills_url = reverse("projects:skills_autocomplete")
        cls.add_skill_url = reverse(
            "projects:skills_add",
            kwargs={"project_id": cls.project.pk},
        )
        cls.remove_skill_url = lambda skill_id: reverse(
            "projects:skills_remove",
            kwargs={
                "project_id": cls.project.pk,
                "skill_id": skill_id,
            },
        )


class ProjectListViewTest(TestDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.skill_name = "Python"
        cls.skill = Skill.objects.create(name=cls.skill_name)

    def test_list_returns_200(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    def test_root_redirects_to_list(self):
        resp = self.client.get(reverse("root"))
        self.assertRedirects(
            resp, self.list_url, fetch_redirect_response=False
        )

    def test_project_appears_in_list(self):
        resp = self.client.get(self.list_url)
        self.assertContains(resp, self.project.name)

    def test_skill_filter(self):
        other = create_project(self.owner, name="Other")
        self.project.skills.add(self.skill)
        url = f"{self.list_url}?skill={self.skill_name}"
        resp = self.client.get(url)
        self.assertContains(resp, self.project.name)
        self.assertNotContains(resp, other.name)


class ProjectDetailViewTest(TestDataMixin, TestCase):
    def test_detail_returns_200(self):
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    def test_detail_shows_name(self):
        resp = self.client.get(self.detail_url)
        self.assertContains(resp, self.project.name)

    def test_404_on_nonexistent(self):
        url = reverse("projects:detail", kwargs={"project_id": 99999})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)


class CreateProjectViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.auth_client = self.client_class()
        self.auth_client.force_login(self.user)

    def test_get_create_form_requires_login(self):
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), resp["Location"])

    def test_get_create_form_authorized(self):
        resp = self.auth_client.get(self.create_url)
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    def test_create_project_redirects_to_detail(self):
        data = {
            "name": "New Project",
            "description": "Desc",
            "github_url": "",
            "status": STATUS_OPEN,
        }
        resp = self.auth_client.post(self.create_url, data)
        project = Project.objects.get(name=data["name"])
        detail_url = reverse(
            "projects:detail", kwargs={"project_id": project.pk}
        )
        self.assertRedirects(resp, detail_url)

    def test_owner_set_automatically(self):
        data = {
            "name": "Auto Owner",
            "description": "",
            "github_url": "",
            "status": STATUS_OPEN,
        }
        self.auth_client.post(self.create_url, data)
        project = Project.objects.get(name=data["name"])
        self.assertEqual(project.owner, self.user)

    def test_owner_added_as_participant(self):
        data = {
            "name": "Participant Test",
            "description": "",
            "github_url": "",
            "status": STATUS_OPEN,
        }
        self.auth_client.post(self.create_url, data)
        project = Project.objects.get(name=data["name"])
        self.assertIn(self.user, project.participants.all())

    def test_invalid_github_url_rejected(self):
        data = {
            "name": "Bad Github",
            "description": "",
            "github_url": "https://gitlab.com/user",
            "status": STATUS_OPEN,
        }
        resp = self.auth_client.post(self.create_url, data)
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertFalse(
            Project.objects.filter(name=data["name"]).exists()
        )


class ToggleParticipateTest(TestDataMixin, TestCase):
    def setUp(self):
        self.auth_client = self.client_class()
        self.other_client = self.client_class()
        self.owner_client = self.client_class()
        self.auth_client.force_login(self.other)
        self.other_client.force_login(self.other)
        self.owner_client.force_login(self.owner)

    def test_join_project(self):
        resp = self.auth_client.post(
            self.toggle_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["participant"])
        self.assertIn(self.other, self.project.participants.all())

    def test_leave_project(self):
        self.project.participants.add(self.other)
        resp = self.other_client.post(
            self.toggle_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        data = resp.json()
        self.assertFalse(data["participant"])
        self.assertNotIn(self.other, self.project.participants.all())

    def test_owner_cannot_leave(self):
        resp = self.owner_client.post(
            self.toggle_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.status_code, HTTPStatus.BAD_REQUEST)

    def test_requires_login(self):
        resp = self.client.post(self.toggle_url)
        self.assertEqual(resp.status_code, HTTPStatus.FOUND)
        self.assertIn(reverse("users:login"), resp["Location"])


class CompleteProjectTest(TestDataMixin, TestCase):
    def setUp(self):
        self.owner_client = self.client_class()
        self.other_client = self.client_class()
        self.owner_client.force_login(self.owner)
        self.other_client.force_login(self.other)

    def test_owner_can_complete(self):
        resp = self.owner_client.post(
            self.complete_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.json()["status"], "ok")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_non_owner_cannot_complete(self):
        resp = self.other_client.post(
            self.complete_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)


class ToggleFavoriteTest(TestDataMixin, TestCase):
    def setUp(self):
        self.auth_client = self.client_class()
        self.auth_client.force_login(self.user)

    def test_add_favorite(self):
        resp = self.auth_client.post(
            self.favorite_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertTrue(resp.json()["favorite"])
        self.assertIn(self.user, self.project.favorites.all())

    def test_remove_favorite(self):
        self.project.favorites.add(self.user)
        resp = self.auth_client.post(
            self.favorite_url,
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertFalse(resp.json()["favorite"])
        self.assertNotIn(self.user, self.project.favorites.all())


class SkillsAPITest(TestDataMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.python_skill = Skill.objects.create(name="Python")
        cls.postgresql_skill = Skill.objects.create(name="PostgreSQL")
        cls.pypy_skill = Skill.objects.create(name="PyPy")

    def setUp(self):
        self.owner_client = self.client_class()
        self.other_client = self.client_class()
        self.owner_client.force_login(self.owner)
        self.other_client.force_login(self.other)

    def test_autocomplete_filters_by_prefix(self):
        resp = self.client.get(self.skills_url, {"q": "Py"})
        data = resp.json()
        names = [s["name"] for s in data]
        self.assertIn("Python", names)
        self.assertIn("PyPy", names)
        self.assertNotIn("PostgreSQL", names)

    def test_autocomplete_case_insensitive(self):
        resp = self.client.get(self.skills_url, {"q": "py"})
        names = [s["name"] for s in resp.json()]
        self.assertIn("Python", names)

    def test_autocomplete_returns_max_skin(self):
        for i in range(MAX_SKIN_IN_PAGE + 1):
            Skill.objects.create(name=f"Skill{i:02d}")
        resp = self.client.get(self.skills_url, {"q": "Skill"})
        self.assertEqual(len(resp.json()), MAX_SKIN_IN_PAGE)

    def test_add_existing_skill_by_id(self):
        resp = self.owner_client.post(
            self.add_skill_url,
            data=json.dumps({"skill_id": self.python_skill.pk}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        data = resp.json()
        self.assertTrue(data["added"])
        self.assertFalse(data["created"])
        self.assertIn(self.python_skill, self.project.skills.all())

    def test_add_new_skill_by_name(self):
        resp = self.owner_client.post(
            self.add_skill_url,
            data=json.dumps({"name": "Rust"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["created"])
        self.assertTrue(Skill.objects.filter(name="Rust").exists())

    def test_add_duplicate_skill_added_is_false(self):
        self.project.skills.add(self.python_skill)
        resp = self.owner_client.post(
            self.add_skill_url,
            data=json.dumps({"skill_id": self.python_skill.pk}),
            content_type="application/json",
        )
        self.assertFalse(resp.json()["added"])

    def test_non_owner_cannot_add_skill(self):
        resp = self.other_client.post(
            self.add_skill_url,
            data=json.dumps({"skill_id": self.python_skill.pk}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)

    def test_remove_skill(self):
        self.project.skills.add(self.python_skill)
        remove_url = self.remove_skill_url(self.python_skill.pk)
        resp = self.owner_client.post(
            remove_url, content_type="application/json"
        )
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertNotIn(self.python_skill, self.project.skills.all())
        self.assertTrue(
            Skill.objects.filter(pk=self.python_skill.pk).exists()
        )

    def test_remove_skill_non_owner_forbidden(self):
        self.project.skills.add(self.python_skill)
        remove_url = self.remove_skill_url(self.python_skill.pk)
        resp = self.other_client.post(remove_url)
        self.assertEqual(resp.status_code, HTTPStatus.FORBIDDEN)
