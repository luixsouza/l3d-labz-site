"""Serializers DRF do app de contas."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "display_name", "first_name", "last_name", "email",
                  "phone", "newsletter_opt_in", "date_joined")
        read_only_fields = ("id", "date_joined")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "label", "recipient", "zip_code", "street", "number",
                  "complement", "district", "city", "state", "is_default")
