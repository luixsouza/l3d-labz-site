"""Serializers do carrinho (estrutura de sessão, não-ORM)."""
from __future__ import annotations

from rest_framework import serializers


class CartItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shipping = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
