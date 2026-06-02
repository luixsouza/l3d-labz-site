"""Serviços do núcleo — orquestram dados de outros apps para a home."""
from __future__ import annotations

from typing import Any

from .layers import BaseService


class HomeService(BaseService):
    """Monta o payload da página inicial agregando catálogo e promoções.

    Importa os serviços dos outros apps de forma tardia para não criar
    dependência circular entre apps no momento do import.
    """

    @staticmethod
    def get_homepage_context() -> dict[str, Any]:
        from apps.catalog.services import CatalogService
        from apps.promotions.services import PromotionService

        return {
            "hero_promotion": PromotionService.get_hero_promotion(),
            "categories": CatalogService.list_highlighted_categories(),
            "featured_products": CatalogService.list_featured_products(limit=8),
            "new_arrivals": CatalogService.list_new_arrivals(limit=4),
            "active_promotions": PromotionService.list_active_promotions(limit=3),
        }
