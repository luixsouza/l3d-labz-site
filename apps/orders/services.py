"""Serviços de pedido — orquestram carrinho, estoque, cupom e pagamento."""
from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import F

from apps.cart.services import CartService
from apps.catalog.models import Product
from apps.core.layers import BaseService
from apps.promotions.models import Coupon

from .mappers import OrderMapper
from .models import Order, OrderItem
from .payments import PaymentService
from .queries import OrderQuery


class EmptyCartError(Exception):
    """Tentativa de fechar pedido com carrinho vazio."""


class OrderService(BaseService):
    @staticmethod
    @transaction.atomic
    def create_from_cart(request, data: dict) -> Order:
        cart = CartService.build(request)
        items = cart["items"]
        if not items:
            raise EmptyCartError()
        summary = cart["summary"]

        order = Order.objects.create(
            user=request.user,
            payment_method=data["payment_method"],
            card_last4=data.get("card_last4", ""),
            subtotal=summary["subtotal"],
            discount=summary["discount"],
            shipping=summary["shipping"],
            total=summary["total"],
            coupon_code=summary["coupon_code"] or "",
            recipient=data["recipient"],
            phone=data.get("phone", ""),
            zip_code=data["zip_code"],
            street=data["street"],
            number_addr=data["number_addr"],
            complement=data.get("complement", ""),
            district=data["district"],
            city=data["city"],
            state=data["state"].upper(),
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product_id=line["id"],
                product_name=line["name"],
                unit_price=line["unit_price"],
                quantity=line["quantity"],
                line_total=line["line_total"],
            )
            for line in items
        ])

        # baixa de estoque + métrica de vendas (atômico via F)
        for line in items:
            Product.objects.filter(pk=line["id"]).update(
                stock=F("stock") - line["quantity"],
                sales_count=F("sales_count") + line["quantity"],
            )

        # consumo do cupom
        if order.coupon_code:
            Coupon.objects.filter(code=order.coupon_code).update(used_count=F("used_count") + 1)

        # cobrança (simulada)
        PaymentService.process(order)

        # esvazia o carrinho
        request.cart.clear()
        return order

    # ---- leitura ----
    @staticmethod
    def get_history(user) -> list[dict]:
        return OrderMapper.to_list(OrderQuery.for_user(user))

    @staticmethod
    def get_detail(user, number: str) -> dict[str, Any] | None:
        order = OrderQuery.detail_for_user(user, number)
        if not order:
            return None
        return OrderMapper.to_detail(order)
