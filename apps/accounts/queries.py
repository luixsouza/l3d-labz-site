"""Camada de consultas do app de contas (somente ORM)."""
from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Address

User = get_user_model()


class UserQuery:
    @staticmethod
    def by_email(email: str):
        return User.objects.filter(email__iexact=email).first()


class AddressQuery:
    @staticmethod
    def for_user(user):
        return Address.objects.filter(user=user)

    @staticmethod
    def default_for_user(user):
        return Address.objects.filter(user=user, is_default=True).first()
