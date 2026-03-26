from django.urls import path

from . import views

app_name = "projects"

# ========== ПУБЛИЧНЫЕ СТРАНИЦЫ ==========
urlpatterns = [
    path("list/", views.project_index, name="list"),
    path("<int:project_id>/", views.project_detail, name="detail"),
]

# ========== СОЗДАНИЕ / РЕДАКТИРОВАНИЕ ==========
urlpatterns += [
    path("create-project/", views.project_create_view, name="create"),
    path(
        "<int:project_id>/edit/", views.project_edit_view, name="edit"
    ),
]

# ========== AJAX-ДЕЙСТВИЯ ==========
urlpatterns += [
    path(
        "<int:project_id>/toggle-participate/",
        views.toggle_project_participation,
        name="toggle_participate",
    ),
    path(
        "<int:project_id>/toggle-favorite/",
        views.toggle_project_favorite,
        name="toggle_favorite",
    ),
    path(
        "<int:project_id>/complete/",
        views.close_project,
        name="complete",
    ),
]

# ========== УПРАВЛЕНИЕ НАВЫКАМИ ==========
urlpatterns += [
    path(
        "skills/",
        views.skill_autocomplete,
        name="skills_autocomplete",
    ),
    path(
        "<int:project_id>/skills/add/",
        views.add_project_skill,
        name="skills_add",
    ),
    path(
        "<int:project_id>/skills/<int:skill_id>/remove/",
        views.remove_project_skill,
        name="skills_remove",
    ),
]

# ========== ИЗБРАННОЕ ==========
urlpatterns += [
    path(
        "favorites/", views.favorite_projects_list, name="favorites"
    ),
]
