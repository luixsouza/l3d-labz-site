"""Mappers do catálogo — Model -> dict para template/serializer."""
from __future__ import annotations

from typing import Any

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper

from .models import Category, Product


class CategoryMapper(BaseMapper[Category]):
    @classmethod
    def to_dict(cls, instance: Category) -> dict[str, Any]:
        count = getattr(instance, "num_products", None)
        if count is None:
            count = instance.products.filter(is_active=True).count()
        return {
            "name": instance.name,
            "slug": instance.slug,
            "icon": instance.icon,
            "accent": instance.accent,
            "product_count": count,
            "url": instance.get_absolute_url(),
        }


class ProductMapper(BaseMapper[Product]):
    @classmethod
    def to_dict(cls, instance: Product) -> dict[str, Any]:
        return {
            "id": instance.id,
            "name": instance.name,
            "slug": instance.slug,
            "category_name": instance.category.name,
            "category_slug": instance.category.slug,
            "icon": instance.category.icon,
            "accent": instance.category.accent,
            "monogram": instance.name[:1].upper(),
            "image_url": instance.image.url if instance.image else (instance.image_url or ""),
            "price": instance.price,
            # Preço 0 = produzido sob demanda (orçamento no Instagram), não "R$ 0,00".
            "price_display": format_brl(instance.price) if instance.price > 0 else "Sob consulta",
            "on_demand": instance.price <= 0,
            "old_price_display": format_brl(instance.compare_at_price) if instance.has_discount else "",
            "has_discount": instance.has_discount,
            "discount_pct": instance.discount_pct,
            "is_new": instance.is_new,
            "in_stock": instance.in_stock,
            "rating": float(instance.rating),
            "url": instance.get_absolute_url(),
            # Campos 3D — usados no hero da home e na galeria de modelos.
            "has_3d": instance.has_3d_model,
            "has_stl": instance.has_stl,
            "model_3d_url": instance.model_3d.url if instance.model_3d else "",
            "model_stl_url": instance.model_stl.url if instance.model_stl else "",
            # Specs de filamento (extraídas do 3MF via extrair_specs_3mf).
            "filament_grams": instance.filament_grams,
            "color_count": instance.color_count,
            "filament_display": f"{instance.filament_grams} g" if instance.filament_grams else "",
        }

    @classmethod
    def to_detail(cls, instance: Product) -> dict[str, Any]:
        data = cls.to_dict(instance)
        # Galeria: foto principal primeiro, depois imagens extras ordenadas por order.
        foto_principal = instance.image.url if instance.image else (instance.image_url or "")
        extras = [img.image.url for img in instance.gallery.all() if img.image]
        gallery = [url for url in ([foto_principal] + extras) if url]
        data.update(
            {
                "description": instance.description,
                "material": instance.material,
                "dimensions": instance.dimensions,
                "print_time_hours": instance.print_time_hours,
                "stock": instance.stock,
                "sales_count": instance.sales_count,
                "gallery": gallery,
            }
        )
        return data
