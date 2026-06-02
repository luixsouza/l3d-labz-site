"""Disponibiliza o resumo do carrinho (contador) em todos os templates."""
from __future__ import annotations


def cart_summary(request):
    cart = getattr(request, "cart", None)
    return {"cart_count": cart.total_quantity if cart else 0}
