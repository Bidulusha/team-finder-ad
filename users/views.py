from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ChangePasswordForm,
    EditProfileForm,
    LoginForm,
    RegistrationForm,
)
from .models import User
from team_finder.service import paginator

# ─── Auth ────────────────────────────────────────────────────────────────────


def register(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(
            email=d["email"],
            name=d["name"],
            surname=d["surname"],
            password=d["password"],
        )
        login(request, user)
        return redirect("projects:list")
    
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request.POST or None, request=request or None)
    if form.is_valid():
        login(request, form.get_user())
        return redirect("projects:list")

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


# ─── Profile ─────────────────────────────────────────────────────────────────


def profile_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": user})


def users_list(request):
    all_users = User.objects.filter(is_active=True).order_by("id")
    page_obj = paginator(all_users, request, "page")
    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj,
            "page_obj": page_obj,
        },
    )


@login_required
def edit_profile(request):
    user = request.user
    form = EditProfileForm(request.POST or None, request.FILES or None, instance=user, current_user_id=user.pk)

    if form.is_valid():
        # Если новый аватар не загружен — оставляем старый
        if not request.FILES.get("avatar"):
            form.instance.avatar = user.avatar
        form.save()
        return redirect("users:profile_detail", user_id = user.pk)

    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    user = request.user
    form = ChangePasswordForm(request.POST or None, user=user)

    if form.is_valid():
        user.set_password(form.cleaned_data["new_password1"])
        user.save()
        update_session_auth_hash(
            request, user
        )  # не разлогинивать
        return redirect("users:profile_detail", user_id = user.pk)

    return render(
        request, "users/change_password.html", {"form": form}
    )
