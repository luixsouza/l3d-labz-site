"""Helpers de formatação reutilizáveis."""
from __future__ import annotations

from decimal import Decimal


def format_brl(value: Decimal | float | int | None) -> str:
    """Formata um valor como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    if value is None:
        return "—"
    value = Decimal(value)
    inteiro, _, decimal = f"{value:.2f}".partition(".")
    sinal = "-" if inteiro.startswith("-") else ""
    inteiro = inteiro.lstrip("-")
    # agrupa milhares com ponto
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return f"{sinal}R$ {'.'.join(grupos)},{decimal}"
