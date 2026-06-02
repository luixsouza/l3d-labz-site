"""Consultas do carrinho — busca os produtos referenciados na sessão."""
from __future__ import annotations

from apps.catalog.models import Product


class CartQuery:
    @staticmethod
    def products_by_ids(ids) -> dict[int, Product]:
        """Retorna {id: Product} apenas dos produtos ativos (1 query)."""
        qs = Product.objects.active().with_relations().filter(id__in=list(ids))
        return {p.id: p for p in qs}
