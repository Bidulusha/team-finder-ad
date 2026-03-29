from django import forms

from team_finder.constants import STATUS_CHOICES
from team_finder.validators import validate_github_link
from projects.models import Project


# ========== PROJECT FORM ==========
class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Название проекта"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Опишите проект..."}
            ),
            "github_url": forms.URLInput(
                attrs={"placeholder": "https://github.com/..."}
            ),
            "status": forms.Select(choices=STATUS_CHOICES),
        }

    def clean_github_url(self):
        return validate_github_link(
            self.cleaned_data.get("github_url", "")
        )
