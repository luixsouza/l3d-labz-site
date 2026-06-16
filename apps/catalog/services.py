"""Serviços do catálogo — orquestram queries + mappers para as views."""
from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator

from apps.core.layers import BaseService

from .mappers import CategoryMapper, ProductMapper
from .queries import CategoryQuery, ProductQuery

PAGE_SIZE = 24


class CatalogService(BaseService):
    # ---- home ----
    @staticmethod
    def list_highlighted_categories() -> list[dict]:
        return CategoryMapper.to_list(CategoryQuery.highlighted())

    @staticmethod
    def list_featured_products(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.featured(limit))

    @staticmethod
    def list_new_arrivals(limit: int = 4) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.new_arrivals(limit))

    @staticmethod
    def list_on_sale(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.on_sale(limit))

    # ---- hero da home: produto 3D em destaque ----
    @staticmethod
    def get_hero_3d_product() -> dict[str, Any] | None:
        """Retorna o modelo 3D da vitrine do hero da home ou None.

        Prioridade:
        (1) settings.HERO_3D_MODEL_URL — modelo-vitrine geek (não-produto),
            GLB auto-hospedado, mostrado como demo da marca;
        (2) settings.HERO_3D_PRODUCT_SLUG — produto-3D curado a dedo;
        (3) um destaque (is_featured) com model_3d;
        (4) o primeiro com model_3d (maior sales_count).
        """
        from django.conf import settings
        from django.templatetags.static import static

        # (1) modelo-vitrine geek (não-produto)
        showcase_url = (getattr(settings, "HERO_3D_MODEL_URL", "") or "").strip()
        if showcase_url:
            src = showcase_url if showcase_url.startswith(("http://", "https://", "/")) else static(showcase_url)
            return {
                "name": getattr(settings, "HERO_3D_MODEL_ALT", "Modelo 3D"),
                "model_3d_url": src,
                "image_url": "",       # sem poster: o pedestal claro do card cobre o load
                "has_stl": False,
                "model_stl_url": "",
                "is_showcase": True,
            }

        # (2-4) produto-3D do catálogo
        candidates = ProductQuery.with_3d(limit=20)
        if not candidates:
            return None
        curated_slug = getattr(settings, "HERO_3D_PRODUCT_SLUG", "") or ""
        curated = next((p for p in candidates if p.slug == curated_slug), None)
        featured = next((p for p in candidates if p.is_featured), None)
        produto = curated or featured or candidates[0]
        return ProductMapper.to_dict(produto)

    # ---- catálogo (listagem com filtros + paginação) ----
    @staticmethod
    def browse(params, page: int = 1, only_3d: bool = False) -> dict[str, Any]:
        """Monta o contexto completo do catálogo (paginação + filtros + ordenação).

        only_3d=True restringe aos produtos com model_3d, usado pela página /modelos-3d/.
        """
        category_slug = params.get("categoria") or None
        query = params.get("q") or None
        sort = params.get("sort") or "relevance"
        material = params.get("material") or None
        min_price = _to_decimal(params.get("min"))
        max_price = _to_decimal(params.get("max"))
        color = params.get("color") or None
        filament = params.get("filament") or None

        qs = ProductQuery.search(
            category_slug=category_slug,
            query=query,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
            material=material,
            only_3d=only_3d,
            color=color,
            filament=filament,
        )
        paginator = Paginator(qs, PAGE_SIZE)
        page_obj = paginator.get_page(page)

        active_category = None
        if category_slug:
            cat = CategoryQuery.by_slug(category_slug)
            active_category = CategoryMapper.to_dict(cat) if cat else None

        from apps.promotions.services import PromotionService

        return {
            "products": ProductMapper.to_list(page_obj.object_list),
            "page_obj": page_obj,
            "paginator": paginator,
            "total": paginator.count,
            "categories": CategoryMapper.to_list(CategoryQuery.all_with_counts()),
            "active_category": active_category,
            "current_sort": sort,
            "materials": ProductQuery.materials(),
            "specs_ready": ProductQuery.specs_available(),
            "active_material": material or "",
            "query": query or "",
            "only_3d": only_3d,
            "active_color": color or "",
            "active_filament": filament or "",
            "promotions": PromotionService.list_active_promotions(limit=5),
            "flash_sale": ProductMapper.to_list(ProductQuery.on_sale(8)),
            "best_sellers": ProductMapper.to_list(ProductQuery.featured(6)),
        }

    # ---- detalhe ----
    @staticmethod
    def get_detail(slug: str) -> dict[str, Any] | None:
        product = ProductQuery.detail_by_slug(slug)
        if not product:
            return None
        return {
            "product": ProductMapper.to_detail(product),
            "related": ProductMapper.to_list(ProductQuery.related(product)),
        }


def _to_decimal(value):
    if not value:
        return None
    try:
        from decimal import Decimal

        return Decimal(str(value).replace(",", "."))
    except (ValueError, ArithmeticError):
        return None
