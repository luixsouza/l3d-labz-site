"""Pagamento — SIMULADO.

Isola a lógica de cobrança para que, no futuro, baste trocar o corpo de
`process()` por uma chamada a um gateway real (Mercado Pago, Stripe, etc.)
sem tocar no restante do app.
"""
from __future__ import annotations

from django.utils import timezone

from .models import Order


class PaymentService:
    @staticmethod
    def process(order: Order) -> None:
        """Simula a cobrança e atualiza o status do pedido.

        PIX e cartão são aprovados na hora; boleto fica pendente até "compensar".
        """
        if order.payment_method in (Order.Payment.PIX, Order.Payment.CREDIT_CARD):
            order.payment_status = Order.PaymentStatus.APPROVED
            order.status = Order.Status.PROCESSING
            order.paid_at = timezone.now()
        else:  # boleto
            order.payment_status = Order.PaymentStatus.PENDING
            order.status = Order.Status.PENDING
        order.save(update_fields=["payment_status", "status", "paid_at"])

    # ---- artefatos de pagamento (fake, só para a tela de confirmação) ----
    @staticmethod
    def pix_payload(order: Order) -> str:
        valor = f"{order.total:.2f}"
        return (
            f"00020126580014BR.GOV.BCB.PIX0136nexora-{order.number.lower()}"
            f"520400005303986540{len(valor)}{valor}5802BR5906NEXORA6009SAO PAULO"
            f"62070503{order.number[-3:]}6304ABCD"
        )

    @staticmethod
    def boleto_line(order: Order) -> str:
        base = order.number.replace("-", "")
        cents = int(order.total * 100)
        return f"34191.79001 01043.510047 91020.150008 7 0000{cents:010d}{base[-4:]}"
