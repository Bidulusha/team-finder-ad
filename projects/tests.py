import json

from django.test import TestCase

from projects.models import Project, Skill
from users.models import User


# ========== TEST HELPERS ==========
def create_user(
    email="u@example.com",
    name="Test",
    surname="User",
    password="pass1234",
):
    """Создаёт тестового пользователя."""
    return User.objects.create_user(
        email=email, name=name, surname=surname, password=password
    )


def create_project(owner, name="Test Project", status="open"):
    """Создаёт тестовый проект и добавляет владельца в участники."""
    project = Project.objects.create(
        name=name, owner=owner, status=status
    )
    project.participants.add(owner)
    return project


# ========== PROJECT LIST VIEW TESTS ==========
class ProjectListViewTest(TestCase):
    def setUp(self):
        self.owner = create_user()
        self.project = create_project(self.owner)

    def test_list_returns_200(self):
        resp = self.client.get("/projects/list/")
        self.assertEqual(resp.status_code, 200)

    def test_root_redirects_to_list(self):
        resp = self.client.get("/")
        self.assertRedirects(
            resp, "/projects/list/", fetch_redirect_response=False
        )

    def test_project_appears_in_list(self):
        resp = self.client.get("/projects/list/")
        self.assertContains(resp, self.project.name)

    def test_skill_filter(self):
        skill = Skill.objects.create(name="Python")
        other = create_project(self.owner, name="Other")
        self.project.skills.add(skill)

        resp = self.client.get("/projects/list/?skill=Python")
        self.assertContains(resp, self.project.name)
        self.assertNotContains(resp, "Other")


# ========== PROJECT DETAIL VIEW TESTS ==========
class ProjectDetailViewTest(TestCase):
    def setUp(self):
        self.owner = create_user()
        self.project = create_project(self.owner)

    def test_detail_returns_200(self):
        resp = self.client.get(f"/projects/{self.project.pk}/")
        self.assertEqual(resp.status_code, 200)

    def test_detail_shows_name(self):
        resp = self.client.get(f"/projects/{self.project.pk}/")
        self.assertContains(resp, self.project.name)

    def test_404_on_nonexistent(self):
        resp = self.client.get("/projects/99999/")
        self.assertEqual(resp.status_code, 404)


# ========== CREATE PROJECT VIEW TESTS ==========
class CreateProjectViewTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_login(self.user)

    def test_get_create_form(self):
        resp = self.client.get("/projects/create-project/")
        self.assertEqual(resp.status_code, 200)

    def test_create_project_redirects_to_detail(self):
        resp = self.client.post(
            "/projects/create-project/",
            {
                "name": "New Project",
                "description": "Desc",
                "github_url": "",
                "status": "open",
            },
        )
        project = Project.objects.get(name="New Project")
        self.assertRedirects(resp, f"/projects/{project.pk}/")

    def test_owner_set_automatically(self):
        self.client.post(
            "/projects/create-project/",
            {
                "name": "Auto Owner",
                "description": "",
                "github_url": "",
                "status": "open",
            },
        )
        project = Project.objects.get(name="Auto Owner")
        self.assertEqual(project.owner, self.user)

    def test_owner_added_as_participant(self):
        self.client.post(
            "/projects/create-project/",
            {
                "name": "Participant Test",
                "description": "",
                "github_url": "",
                "status": "open",
            },
        )
        project = Project.objects.get(name="Participant Test")
        self.assertIn(self.user, project.participants.all())

    def test_create_requires_login(self):
        self.client.logout()
        resp = self.client.get("/projects/create-project/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/users/login/", resp["Location"])

    def test_invalid_github_url_rejected(self):
        resp = self.client.post(
            "/projects/create-project/",
            {
                "name": "Bad Github",
                "description": "",
                "github_url": "https://gitlab.com/user",
                "status": "open",
            },
        )
        self.assertEqual(
            resp.status_code, 200
        )  # форма вернулась с ошибкой
        self.assertFalse(
            Project.objects.filter(name="Bad Github").exists()
        )


# ========== TOGGLE PARTICIPATION TESTS ==========
class ToggleParticipateTest(TestCase):
    def setUp(self):
        self.owner = create_user(email="owner@x.com")
        self.other = create_user(email="other@x.com")
        self.project = create_project(self.owner)

    def _post(self, user, project_id):
        self.client.force_login(user)
        return self.client.post(
            f"/projects/{project_id}/toggle-participate/",
            content_type="application/json",
            data=json.dumps({}),
        )

    def test_join_project(self):
        resp = self._post(self.other, self.project.pk)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["participant"])
        self.assertIn(self.other, self.project.participants.all())

    def test_leave_project(self):
        self.project.participants.add(self.other)
        resp = self._post(self.other, self.project.pk)
        data = resp.json()
        self.assertFalse(data["participant"])
        self.assertNotIn(self.other, self.project.participants.all())

    def test_owner_cannot_leave(self):
        resp = self._post(self.owner, self.project.pk)
        self.assertEqual(resp.status_code, 400)

    def test_requires_login(self):
        resp = self.client.post(
            f"/projects/{self.project.pk}/toggle-participate/"
        )
        self.assertEqual(resp.status_code, 302)


# ========== COMPLETE PROJECT TESTS ==========
class CompleteProjectTest(TestCase):
    def setUp(self):
        self.owner = create_user(email="owner@x.com")
        self.other = create_user(email="other@x.com")
        self.project = create_project(self.owner)

    def test_owner_can_complete(self):
        self.client.force_login(self.owner)
        resp = self.client.post(
            f"/projects/{self.project.pk}/complete/",
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.json()["status"], "ok")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_non_owner_cannot_complete(self):
        self.client.force_login(self.other)
        resp = self.client.post(
            f"/projects/{self.project.pk}/complete/",
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertEqual(resp.status_code, 403)


# ========== TOGGLE FAVORITE TESTS ==========
class ToggleFavoriteTest(TestCase):
    def setUp(self):
        self.user = create_user()
        self.owner = create_user(email="owner@x.com")
        self.project = create_project(self.owner)
        self.client.force_login(self.user)

    def test_add_favorite(self):
        resp = self.client.post(
            f"/projects/{self.project.pk}/toggle-favorite/",
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertTrue(resp.json()["favorite"])
        self.assertIn(self.user, self.project.favorites.all())

    def test_remove_favorite(self):
        self.project.favorites.add(self.user)
        resp = self.client.post(
            f"/projects/{self.project.pk}/toggle-favorite/",
            content_type="application/json",
            data=json.dumps({}),
        )
        self.assertFalse(resp.json()["favorite"])
        self.assertNotIn(self.user, self.project.favorites.all())


# ========== SKILLS API TESTS ==========
class SkillsAPITest(TestCase):
    def setUp(self):
        self.owner = create_user()
        self.other = create_user(email="other@x.com")
        self.project = create_project(self.owner)
        Skill.objects.create(name="Python")
        Skill.objects.create(name="PostgreSQL")
        Skill.objects.create(name="PyPy")

    def test_autocomplete_filters_by_prefix(self):
        resp = self.client.get("/projects/skills/?q=Py")
        data = resp.json()
        names = [s["name"] for s in data]
        self.assertIn("Python", names)
        self.assertIn("PyPy", names)
        self.assertNotIn("PostgreSQL", names)

    def test_autocomplete_case_insensitive(self):
        resp = self.client.get("/projects/skills/?q=py")
        names = [s["name"] for s in resp.json()]
        self.assertIn("Python", names)

    def test_autocomplete_returns_max_10(self):
        for i in range(15):
            Skill.objects.create(name=f"Skill{i:02d}")
        resp = self.client.get("/projects/skills/?q=Skill")
        self.assertLessEqual(len(resp.json()), 10)

    def test_add_existing_skill_by_id(self):
        self.client.force_login(self.owner)
        skill = Skill.objects.get(name="Python")
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/add/",
            data=json.dumps({"skill_id": skill.pk}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["added"])
        self.assertFalse(data["created"])
        self.assertIn(skill, self.project.skills.all())

    def test_add_new_skill_by_name(self):
        self.client.force_login(self.owner)
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/add/",
            data=json.dumps({"name": "Rust"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["created"])
        self.assertTrue(Skill.objects.filter(name="Rust").exists())

    def test_add_duplicate_skill_added_is_false(self):
        self.client.force_login(self.owner)
        skill = Skill.objects.get(name="Python")
        self.project.skills.add(skill)
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/add/",
            data=json.dumps({"skill_id": skill.pk}),
            content_type="application/json",
        )
        self.assertFalse(resp.json()["added"])

    def test_non_owner_cannot_add_skill(self):
        self.client.force_login(self.other)
        skill = Skill.objects.get(name="Python")
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/add/",
            data=json.dumps({"skill_id": skill.pk}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_remove_skill(self):
        self.client.force_login(self.owner)
        skill = Skill.objects.get(name="Python")
        self.project.skills.add(skill)
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/{skill.pk}/remove/",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(skill, self.project.skills.all())
        self.assertTrue(Skill.objects.filter(pk=skill.pk).exists())

    def test_remove_skill_non_owner_forbidden(self):
        self.client.force_login(self.other)
        skill = Skill.objects.get(name="Python")
        self.project.skills.add(skill)
        resp = self.client.post(
            f"/projects/{self.project.pk}/skills/{skill.pk}/remove/",
        )
        self.assertEqual(resp.status_code, 403)
