"""Modelos base reutilizáveis."""
from __future__ import annotations

from django.db import models


class TimeStampedModel(models.Model):
    """Base abstrata com timestamps de criação/atualização."""

    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
