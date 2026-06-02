"""Invalida o cache de listagens quando o catálogo muda."""
from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Product
from .queries import invalidate_catalog_cache


@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Category)
def _bust_catalog_cache(sender, **kwargs):
    invalidate_catalog_cache()
