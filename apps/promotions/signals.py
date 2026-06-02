"""Invalida cache de promoções em mudanças."""
from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Promotion
from .queries import invalidate_promotion_cache


@receiver([post_save, post_delete], sender=Promotion)
def _bust_promo_cache(sender, **kwargs):
    invalidate_promotion_cache()
