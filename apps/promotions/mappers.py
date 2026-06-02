"""Mappers de promoções."""
from __future__ import annotations

from typing import Any

from apps.core.layers import BaseMapper

from .models import Promotion


class PromotionMapper(BaseMapper[Promotion]):
    @classmethod
    def to_dict(cls, instance: Promotion) -> dict[str, Any]:
        return {
            "kind": instance.kind,
            "title": instance.title,
            "subtitle": instance.subtitle,
            "badge": instance.badge,
            "cta_label": instance.cta_label,
            "cta_url": instance.cta_url,
            "image_url": instance.image.url if instance.image else (instance.image_url or ""),
            "ends_at": instance.ends_at,
        }
