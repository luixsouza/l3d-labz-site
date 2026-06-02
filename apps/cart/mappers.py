"""Mappers do carrinho — monta linhas e resumo para o template."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.catalog.models import Product
from apps.core.formatting import format_brl


class CartItemMapper:
    @classmethod
    def to_line(cls, product: Product, quantity: int) -> dict[str, Any]:
        line_total = product.price * quantity
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "icon": product.category.icon,
            "accent": product.category.accent,
            "monogram": product.name[:1].upper(),
            "image_url": product.image.url if product.image else (product.image_url or ""),
            "url": product.get_absolute_url(),
            "unit_price": product.price,
            "unit_price_display": format_brl(product.price),
            "quantity": quantity,
            "max_qty": product.stock,
            "line_total": line_total,
            "line_total_display": format_brl(line_total),
        }


class CartSummaryMapper:
    @classmethod
    def to_summary(cls, *, subtotal: Decimal, discount: Decimal, shipping: Decimal,
                   coupon_code: str | None, count: int) -> dict[str, Any]:
        total = subtotal - discount + shipping
        return {
            "count": count,
            "subtotal": subtotal,
            "subtotal_display": format_brl(subtotal),
            "discount": discount,
            "discount_display": format_brl(discount),
            "has_discount": discount > 0,
            "shipping": shipping,
            "shipping_display": "Grátis" if shipping == 0 else format_brl(shipping),
            "is_free_shipping": shipping == 0,
            "total": total,
            "total_display": format_brl(total),
            "coupon_code": coupon_code,
        }
