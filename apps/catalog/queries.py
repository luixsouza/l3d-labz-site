"""Camada de consultas do catálogo — ORM otimizado + cache.

Toda leitura passa por aqui. Listagens "estáveis" (destaques, categorias,
lançamentos) são cacheadas; a busca filtrada usa TTL curto.
"""
from __future__ import annotations

from django.db.models import Count, F, Q

from apps.core import cache as cache_utils

from .models import Category, Product

NS_FEATURED = "catalog:featured"
NS_NEW = "catalog:new"
NS_CATEGORIES = "catalog:categories"
NS_PRODUCT = "catalog:product"
NS_RELATED = "catalog:related"


class CategoryQuery:
    @staticmethod
    def highlighted() -> list[Category]:
        def producer():
            qs = (
                Category.objects.filter(is_highlighted=True)
                .annotate(num_products=Count("products", filter=Q(products__is_active=True)))
                .order_by("order", "name")
            )
            return list(qs)

        return cache_utils.get_or_set(NS_CATEGORIES, producer, bucket="long")

    @staticmethod
    def all_with_counts() -> list[Category]:
        qs = (
            Category.objects.annotate(
                num_products=Count("products", filter=Q(products__is_active=True))
            ).order_by("order", "name")
        )
        return list(qs)

    @staticmethod
    def by_slug(slug: str) -> Category | None:
        return Category.objects.filter(slug=slug).first()


class ProductQuery:
    @staticmethod
    def featured(limit: int = 8) -> list[Product]:
        def producer():
            qs = Product.objects.active().with_relations().filter(is_featured=True)
            return list(qs.order_by("-sales_count")[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_FEATURED, limit), producer, bucket="medium"
        )

    @staticmethod
    def new_arrivals(limit: int = 4) -> list[Product]:
        def producer():
            qs = Product.objects.active().with_relations().order_by("-created_at")
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_NEW, limit), producer, bucket="medium"
        )

    @staticmethod
    def on_sale(limit: int = 8) -> list[Product]:
        def producer():
            qs = (
                Product.objects.active().with_relations()
                .filter(compare_at_price__isnull=False, compare_at_price__gt=F("price"))
                .order_by("-sales_count")
            )
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key("catalog:onsale", limit), producer, bucket="medium"
        )

    @staticmethod
    def detail_by_slug(slug: str) -> Product | None:
        def producer():
            return Product.objects.active().with_relations().filter(slug=slug).first()

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_PRODUCT, slug), producer, bucket="medium"
        )

    @staticmethod
    def related(product: Product, limit: int = 4) -> list[Product]:
        def producer():
            qs = (
                Product.objects.active()
                .with_relations()
                .filter(category=product.category)
                .exclude(pk=product.pk)
                .order_by("-sales_count")
            )
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_RELATED, product.pk, limit), producer, bucket="medium"
        )

    @staticmethod
    def search(*, category_slug=None, query=None, sort="relevance", min_price=None, max_price=None):
        """Busca filtrada — retorna um QuerySet (a view pagina). TTL curto via service."""
        qs = Product.objects.active().with_relations()
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        ordering = {
            "new": "-created_at",
            "popular": "-sales_count",
            "price_asc": "price",
            "price_desc": "-price",
            "relevance": "-is_featured",
        }.get(sort, "-is_featured")
        return qs.order_by(ordering, "-sales_count")


def invalidate_catalog_cache() -> None:
    """Limpa as listagens estáveis. Chamado pelos signals em save/delete."""
    cache_utils.invalidate(
        NS_CATEGORIES,
        cache_utils.build_key(NS_FEATURED, 8),
        cache_utils.build_key(NS_NEW, 4),
        cache_utils.build_key(NS_NEW, 8),
    )
