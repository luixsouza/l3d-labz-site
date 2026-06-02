"""Views do núcleo — finas, delegam ao service."""
from __future__ import annotations

from django.views.generic import TemplateView

from .services import HomeService


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(HomeService.get_homepage_context())
        return context


class AboutView(TemplateView):
    template_name = "core/about.html"
