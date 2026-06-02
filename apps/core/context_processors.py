"""Context processors globais."""
from django.conf import settings


def site_settings(request):
    """Disponibiliza dados de marca em todos os templates."""
    return {"SITE": settings.SITE}
