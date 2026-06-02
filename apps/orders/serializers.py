"""Serializers de pedido (DRF)."""
from __future__ import annotations

from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ("product_name", "unit_price", "quantity", "line_total")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "number", "status", "status_label", "payment_method", "payment_status",
            "subtotal", "discount", "shipping", "total", "coupon_code",
            "recipient", "city", "state", "created_at", "items",
        )
        read_only_fields = fields
