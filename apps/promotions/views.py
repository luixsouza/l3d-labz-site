"""Views de promoções."""
from __future__ import annotations

from django.shortcuts import render

from .services import PromotionService


def promotion_list(request):
    from apps.catalog.services import CatalogService

    context = {
        "promotions": PromotionService.list_active_promotions(limit=12),
        "on_sale": CatalogService.list_on_sale(limit=8),
    }
    return render(request, "promotions/list.html", context)
