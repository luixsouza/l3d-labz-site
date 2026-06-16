"""Camada de consultas do catálogo — ORM otimizado + cache.

Toda leitura passa por aqui. Listagens "estáveis" (destaques, categorias,
lançamentos) são cacheadas; a busca filtrada usa TTL curto.
"""
from __future__ import annotations

from django.db.models import Case, Count, F, IntegerField, Q, Value, When

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
    def with_3d(limit: int | None = None) -> list[Product]:
        qs = (
            Product.objects.active().with_relations()
            .exclude(model_3d="")
            .order_by("-sales_count")
        )
        return list(qs[:limit]) if limit else list(qs)

    @staticmethod
    def detail_by_slug(slug: str) -> Product | None:
        def producer():
            return (
                Product.objects.active()
                .with_relations()
                .prefetch_related("gallery")
                .filter(slug=slug)
                .first()
            )

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
    def search(
        *,
        category_slug=None,
        query=None,
        sort="relevance",
        min_price=None,
        max_price=None,
        material=None,
        only_3d=False,
        color=None,
        filament=None,
    ):
        """Busca filtrada — retorna um QuerySet (a view pagina). TTL curto via service.

        Novos parâmetros:
        - only_3d: filtra apenas produtos com model_3d preenchido.
        - color: "1"/"2"/"3"/"4" — nº de cores ("4" = 4+ cores).
        - filament: faixa de filamento em gramas ("0-50"/"50-150"/"150+");
          produtos com filament_grams=0 (desconhecido) nunca casam.
        """
        qs = Product.objects.active().with_relations()

        # --- filtros básicos ---
        if only_3d:
            qs = qs.exclude(model_3d="")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if material:
            qs = qs.filter(material=material)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        # --- filtro por nº de cores ---
        if color is not None:
            try:
                n = int(color)
                if n >= 4:
                    qs = qs.filter(color_count__gte=4)
                else:
                    qs = qs.filter(color_count=n)
            except (ValueError, TypeError):
                pass  # valor não-numérico → ignorar

        # --- filtro por faixa de filamento (desconhecido = filament_grams=0 nunca casa) ---
        if filament == "0-50":
            qs = qs.filter(filament_grams__gt=0, filament_grams__lte=50)
        elif filament == "50-150":
            qs = qs.filter(filament_grams__gt=50, filament_grams__lte=150)
        elif filament == "150+":
            qs = qs.filter(filament_grams__gt=150)

        # --- ordenação ---
        # Para filament_asc/desc: zeros (desconhecido) sempre ao fim via campo anotado.
        if sort in ("filament_asc", "filament_desc"):
            # _unknown_fil=1 quando filament_grams=0 (desconhecido), 0 caso contrário.
            # order_by sempre coloca os zeros por último, independente da direção.
            qs = qs.annotate(
                _unknown_fil=Case(
                    When(filament_grams=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            if sort == "filament_asc":
                return qs.order_by("_unknown_fil", "filament_grams", "-sales_count")
            else:  # filament_desc
                return qs.order_by("_unknown_fil", "-filament_grams", "-sales_count")

        if sort == "colors_desc":
            # color_count tem default=1 — não há "desconhecido", não precisa do truque.
            return qs.order_by("-color_count", "-sales_count")

        ordering = {
            "new": "-created_at",
            "popular": "-sales_count",
            "price_asc": "price",
            "price_desc": "-price",
            "relevance": "-is_featured",
        }.get(sort, "-is_featured")
        return qs.order_by(ordering, "-sales_count")

    @staticmethod
    def materials() -> list[str]:
        """Materiais distintos dos produtos ativos (para o filtro)."""
        return sorted(
            m for m in Product.objects.active().order_by("material")
            .values_list("material", flat=True).distinct() if m
        )

    @staticmethod
    def specs_available() -> bool:
        """True se algum produto ativo já tem gramas de filamento conhecidas.

        Controla a exibição dos filtros de filamento/cores na UI: enquanto
        `extrair_specs_3mf` não rodou (tudo em filament_grams=0), os filtros
        ficam escondidos por não terem dado; quando a extração popular os
        specs, voltam a aparecer automaticamente (sem deploy). TTL curto.
        """
        def producer():
            return Product.objects.active().filter(filament_grams__gt=0).exists()

        return cache_utils.get_or_set("catalog:specs_available", producer, bucket="short")


def invalidate_catalog_cache() -> None:
    """Limpa as listagens estáveis. Chamado pelos signals em save/delete."""
    cache_utils.invalidate(
        NS_CATEGORIES,
        cache_utils.build_key(NS_FEATURED, 8),
        cache_utils.build_key(NS_NEW, 4),
        cache_utils.build_key(NS_NEW, 8),
    )
