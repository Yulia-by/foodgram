from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import LinkModel


@require_GET
def load_url(request, url_hash: str) -> HttpResponse:
    """Перенаправление с короткой ссылки на оригинальную."""
    link = get_object_or_404(LinkModel, url_hash=url_hash)
    return HttpResponseRedirect(link.original_url)
