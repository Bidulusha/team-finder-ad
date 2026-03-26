from django import forms
from django.core.exceptions import ValidationError

from .models import Project


# ========== VALIDATION ==========
def _validate_github_link(url: str) -> str:
    if not url:
        return url

    allowed_prefixes = (
        "http://github.com/",
        "https://github.com/",
        "http://www.github.com/",
        "https://www.github.com/",
    )
    if not url.startswith(allowed_prefixes):
        raise ValidationError(
            "Ссылка должна вести на GitHub (https://github.com/...)."
        )
    return url


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
            "status": forms.Select(
                choices=[("open", "Открыт"), ("closed", "Закрыт")]
            ),
        }

    def clean_github_url(self):
        return _validate_github_link(
            self.cleaned_data.get("github_url", "")
        )
