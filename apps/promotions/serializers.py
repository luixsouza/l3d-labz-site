"""Serializers de promoções."""
from __future__ import annotations

from rest_framework import serializers

from .models import Coupon, Promotion


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ("id", "kind", "title", "subtitle", "badge", "cta_label", "cta_url", "image", "ends_at")


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ("code", "discount_type", "value", "min_order", "valid_until")
