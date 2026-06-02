"""Modelos de promoções e cupons."""
from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class PromotionQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return self.filter(
            is_active=True,
        ).filter(
            models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now)
        ).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        )


class Promotion(TimeStampedModel):
    class Kind(models.TextChoices):
        HERO = "hero", "Destaque (home)"
        STRIP = "strip", "Faixa"
        BANNER = "banner", "Banner"

    kind = models.CharField("tipo", max_length=10, choices=Kind.choices, default=Kind.STRIP)
    title = models.CharField("título", max_length=140)
    subtitle = models.CharField("subtítulo", max_length=220, blank=True)
    badge = models.CharField("selo", max_length=40, default="Oferta")
    cta_label = models.CharField("texto do botão", max_length=40, default="Conferir")
    cta_url = models.CharField("link do botão", max_length=200, default="/catalogo/")
    image = models.ImageField("imagem", upload_to="promotions/", blank=True)
    image_url = models.URLField("imagem (URL externa)", max_length=500, blank=True)

    is_active = models.BooleanField("ativa", default=True)
    starts_at = models.DateTimeField("início", null=True, blank=True)
    ends_at = models.DateTimeField("fim", null=True, blank=True)
    order = models.PositiveIntegerField("ordem", default=0)

    objects = PromotionQuerySet.as_manager()

    class Meta:
        verbose_name = "promoção"
        verbose_name_plural = "promoções"
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        return self.title


class Coupon(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percentual (%)"
        FIXED = "fixed", "Valor fixo (R$)"

    code = models.CharField("código", max_length=30, unique=True)
    discount_type = models.CharField("tipo", max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    value = models.DecimalField("valor", max_digits=10, decimal_places=2)
    min_order = models.DecimalField("pedido mínimo", max_digits=10, decimal_places=2, default=Decimal("0"))

    is_active = models.BooleanField("ativo", default=True)
    valid_from = models.DateTimeField("válido de", null=True, blank=True)
    valid_until = models.DateTimeField("válido até", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("limite de usos", null=True, blank=True)
    used_count = models.PositiveIntegerField("usos", default=0)

    class Meta:
        verbose_name = "cupom"
        verbose_name_plural = "cupons"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    # --- regras ---
    def is_valid(self, subtotal: Decimal) -> tuple[bool, str]:
        now = timezone.now()
        if not self.is_active:
            return False, "Cupom inativo."
        if self.valid_from and now < self.valid_from:
            return False, "Cupom ainda não está válido."
        if self.valid_until and now > self.valid_until:
            return False, "Cupom expirado."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "Cupom esgotado."
        if subtotal < self.min_order:
            from apps.core.formatting import format_brl

            return False, f"Pedido mínimo de {format_brl(self.min_order)}."
        return True, "Cupom aplicado!"

    def discount_for(self, subtotal: Decimal) -> Decimal:
        if self.discount_type == self.DiscountType.PERCENT:
            return (subtotal * self.value / Decimal("100")).quantize(Decimal("0.01"))
        return min(self.value, subtotal)
