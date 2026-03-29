from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from users.forms import RegistrationForm, EditProfileForm
from users.models import User


def make_user(
    email="test@example.com",
    name="Test",
    surname="User",
    password="pass1234",
):
    return User.objects.create_user(
        email=email, name=name, surname=surname, password=password
    )


class UserModelTest(TestCase):
    def test_create_user_generates_avatar(self):
        user = make_user()
        self.assertTrue(
            user.avatar, "Avatar should be auto-generated"
        )
        self.assertIn("avatar_", user.avatar.name)

    def test_str(self):
        user = make_user()
        self.assertIn("test@example.com", str(user))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_superuser_flags(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            name="Admin",
            surname="User",
            password="x",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class RegistrationFormTest(TestCase):
    def test_valid_registration(self):
        form = RegistrationForm(
            data={
                "name": "Иван",
                "surname": "Иванов",
                "email": "ivan@example.com",
                "password": "secret123",
            }
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_email_rejected(self):
        make_user(email="dup@example.com")
        form = RegistrationForm(
            data={
                "name": "A",
                "surname": "B",
                "email": "dup@example.com",
                "password": "secret",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class PhoneValidationTest(TestCase):
    def _form(self, phone, user=None):
        data = {
            "name": "A",
            "surname": "B",
            "phone": phone,
            "about": "",
        }
        kw = {"current_user_id": user.pk if user else None}
        return EditProfileForm(data, instance=user, **kw)

    def test_valid_8_format(self):
        make_user()
        f = self._form("89991234567")
        self.assertTrue(f.is_valid(), f.errors)

    def test_valid_plus7_format(self):
        f = self._form("+79991234567")
        self.assertTrue(f.is_valid(), f.errors)

    def test_invalid_format_rejected(self):
        f = self._form("123")
        self.assertFalse(f.is_valid())
        self.assertIn("phone", f.errors)

    def test_normalizes_8_to_plus7(self):
        f = self._form("89161234567")
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.cleaned_data["phone"], "+79161234567")

    def test_duplicate_phone_rejected(self):
        u1 = make_user(email="u1@x.com")
        u1.phone = "+79991234567"
        u1.save()
        u2 = make_user(email="u2@x.com")
        f = self._form("+79991234567", user=u2)
        self.assertFalse(f.is_valid())
        self.assertIn("phone", f.errors)


class GithubUrlValidationTest(TestCase):
    def _form(self, url):
        data = {
            "name": "A",
            "surname": "B",
            "github_url": url,
            "about": "",
        }
        return EditProfileForm(data, current_user_id=None)

    def test_valid_github_url(self):
        f = self._form("https://github.com/username")
        self.assertTrue(f.is_valid(), f.errors)

    def test_non_github_rejected(self):
        f = self._form("https://gitlab.com/user")
        self.assertFalse(f.is_valid())
        self.assertIn("github_url", f.errors)

    def test_empty_github_url_ok(self):
        f = self._form("")
        self.assertTrue(f.is_valid(), f.errors)


class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user(
            email="auth@example.com", password="correct"
        )

    def test_login_page_get(self):
        resp = self.client.get(reverse("users:login"))
        self.assertEqual(resp.status_code, HTTPStatus.OK)

    def test_login_success_redirects(self):
        resp = self.client.post(
            reverse("users:login"),
            {
                "email": "auth@example.com",
                "password": "correct",
            },
        )
        self.assertRedirects(resp, "/projects/list/")

    def test_login_wrong_password(self):
        resp = self.client.post(
            reverse("users:login"),
            {
                "email": "auth@example.com",
                "password": "wrong",
            },
        )
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertContains(resp, "Неверный")

    def test_register_creates_user_and_redirects(self):
        resp = self.client.post(
            reverse(
                "users:register",
            ),
            {
                "name": "Новый",
                "surname": "Юзер",
                "email": "new@example.com",
                "password": "pass1234",
            },
        )
        self.assertRedirects(resp, "/projects/list/")
        self.assertTrue(
            User.objects.filter(email="new@example.com").exists()
        )

    def test_logout_redirects(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("users:logout"))
        self.assertRedirects(resp, "/projects/list/")

    def test_edit_profile_requires_login(self):
        resp = self.client.get(reverse("users:edit_profile"))
        self.assertRedirects(
            resp, "/users/login/?next=/users/edit-profile/"
        )

    def test_profile_detail(self):
        resp = self.client.get(
            reverse(
                "users:profile_detail",
                kwargs={"user_id": self.user.pk},
            )
        )
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertContains(resp, self.user.name)
