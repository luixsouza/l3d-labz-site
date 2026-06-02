"""Serializers DRF do catálogo."""
from __future__ import annotations

from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "emoji", "description")


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    discount_pct = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "description", "price", "compare_at_price",
            "emoji", "image", "stock", "rating", "material", "dimensions",
            "print_time_hours", "is_featured", "category",
            "discount_pct", "has_discount", "in_stock",
        )
