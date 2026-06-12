"""Views do núcleo — finas, delegam ao service."""
from __future__ import annotations

from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Vitrine principal — catálogo em destaque."""
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        from apps.catalog.services import CatalogService
        from apps.promotions.services import PromotionService

        context = super().get_context_data(**kwargs)
        context["featured"] = CatalogService.list_featured_products(8)
        context["new_arrivals"] = CatalogService.list_new_arrivals(4)
        context["home_categories"] = CatalogService.list_highlighted_categories()
        context["hero_promo"] = PromotionService.get_hero_promotion()
        return context


class AboutView(TemplateView):
    """Página institucional — quem somos, como funciona, contato."""
    template_name = "core/about.html"
