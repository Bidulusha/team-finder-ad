import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectCreateForm
from .models import Project, Skill
from .constants import PAGINATION_SIZE


# ========== ПУБЛИЧНЫЕ СТРАНИЦЫ ==========
def project_index(request):
    all_skills = Skill.objects.values_list(
        "name", flat=True
    ).order_by("name")
    active_skill = request.GET.get("skill", "").strip()

    queryset = Project.objects.select_related(
        "owner"
    ).prefetch_related("participants")
    if active_skill:
        queryset = queryset.filter(skills__name=active_skill)

    paginator = Paginator(queryset, PAGINATION_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj,
            "page_obj": page_obj,
            "all_skills": all_skills,
            "active_skill": active_skill,
        },
    )


def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related(
            "participants", "skills"
        ),
        pk=project_id,
    )
    return render(
        request, "projects/project-details.html", {"project": project}
    )


# ========== СОЗДАНИЕ / РЕДАКТИРОВАНИЕ ==========
@login_required
def project_create_view(request):
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(
                request.user
            )  # автор становится участником
            return redirect(f"/projects/{project.pk}/")
    else:
        form = ProjectCreateForm()
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def project_edit_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user and not request.user.is_staff:
        return redirect(f"/projects/{project_id}/")

    if request.method == "POST":
        form = ProjectCreateForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(f"/projects/{project_id}/")
    else:
        form = ProjectCreateForm(instance=project)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


# ========== AJAX: УЧАСТНИКИ ==========
@login_required
@require_POST
def toggle_project_participation(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner == request.user:
        return JsonResponse(
            {
                "status": "error",
                "detail": "Владелец не может покинуть свой проект",
            },
            status=400,
        )

    is_participant = project.participants.filter(
        pk=request.user.pk
    ).exists()
    if is_participant:
        project.participants.remove(request.user)
        return JsonResponse({"status": "ok", "participant": False})
    else:
        project.participants.add(request.user)
        return JsonResponse({"status": "ok", "participant": True})


# ========== AJAX: СТАТУС ПРОЕКТА ==========
@login_required
@require_POST
def close_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user and not request.user.is_staff:
        return JsonResponse({"status": "error"}, status=403)

    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok"})


# ========== AJAX: ИЗБРАННОЕ ==========
@login_required
@require_POST
def toggle_project_favorite(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    is_favorite = project.favorites.filter(
        pk=request.user.pk
    ).exists()
    if is_favorite:
        project.favorites.remove(request.user)
        return JsonResponse({"status": "ok", "favorite": False})
    else:
        project.favorites.add(request.user)
        return JsonResponse({"status": "ok", "favorite": True})


@login_required
def favorite_projects_list(request):
    projects = request.user.favorited_projects.select_related(
        "owner"
    ).prefetch_related("participants")
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": projects},
    )


# ========== AJAX: НАВЫКИ ==========
def skill_autocomplete(request):
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.filter(name__istartswith=query).order_by(
        "name"
    )[:10]
    data = list(skills.values("id", "name"))
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def add_project_skill(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse(
            {"error": "Недостаточно прав"}, status=403
        )

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Невалидный JSON"}, status=400)

    skill_id = body.get("skill_id")
    raw_name = body.get("name", "").strip()

    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
        created = False
    elif raw_name:
        skill, created = Skill.objects.get_or_create(name=raw_name)
    else:
        return JsonResponse(
            {"error": "Укажите skill_id или name"}, status=400
        )

    added = not project.skills.filter(pk=skill.pk).exists()
    if added:
        project.skills.add(skill)

    return JsonResponse(
        {
            "id": skill.pk,
            "name": skill.name,
            "skill_id": skill.pk,
            "created": created,
            "added": added,
        }
    )


@login_required
@require_POST
def remove_project_skill(request, project_id, skill_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse(
            {"error": "Недостаточно прав"}, status=403
        )

    skill = get_object_or_404(Skill, pk=skill_id)
    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})
