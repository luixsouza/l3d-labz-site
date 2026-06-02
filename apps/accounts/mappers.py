"""Mappers do app de contas — Model -> dict para template/serializer."""
from __future__ import annotations

from typing import Any

from apps.core.layers import BaseMapper

from .models import Address, User


class UserMapper(BaseMapper[User]):
    @classmethod
    def to_dict(cls, instance: User) -> dict[str, Any]:
        return {
            "id": instance.id,
            "display_name": instance.display_name,
            "full_name": instance.get_full_name(),
            "email": instance.email,
            "phone": instance.phone,
            "newsletter": instance.newsletter_opt_in,
            "member_since": instance.date_joined,
        }


class AddressMapper(BaseMapper[Address]):
    @classmethod
    def to_dict(cls, instance: Address) -> dict[str, Any]:
        return {
            "id": instance.id,
            "label": instance.label,
            "recipient": instance.recipient,
            "line": f"{instance.street}, {instance.number}"
            + (f" — {instance.complement}" if instance.complement else ""),
            "district": instance.district,
            "city": instance.city,
            "state": instance.state,
            "zip_code": instance.zip_code,
            "is_default": instance.is_default,
        }
