from django.core.paginator import Paginator

from team_finder.constants import PAGINATION_SIZE


def paginator(queryset, request, page_name):
    paginator = Paginator(queryset, PAGINATION_SIZE)
    return paginator.get_page(request.GET.get(page_name))


def normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("8"):
        return "+7" + phone[1:]
    return phone
