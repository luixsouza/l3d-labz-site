"""Serviços de promoções e cupons."""
from __future__ import annotations

from decimal import Decimal

from apps.core.layers import BaseService

from .mappers import PromotionMapper
from .queries import CouponQuery, PromotionQuery


class PromotionService(BaseService):
    @staticmethod
    def get_hero_promotion() -> dict | None:
        promo = PromotionQuery.hero()
        return PromotionMapper.to_dict(promo) if promo else None

    @staticmethod
    def list_active_promotions(limit: int = 6) -> list[dict]:
        return PromotionMapper.to_list(PromotionQuery.active(limit))


class CouponService(BaseService):
    @staticmethod
    def validate(code: str, subtotal: Decimal) -> dict:
        """Valida um cupom para um subtotal. Retorna dict pronto para a view."""
        coupon = CouponQuery.by_code(code)
        if not coupon:
            return {"valid": False, "message": "Cupom não encontrado.", "discount": Decimal("0"), "code": code}
        ok, message = coupon.is_valid(subtotal)
        discount = coupon.discount_for(subtotal) if ok else Decimal("0")
        return {
            "valid": ok,
            "message": message,
            "discount": discount,
            "code": coupon.code,
        }
