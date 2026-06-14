"""Mapper de resultados de precificação — converte floats em strings formatadas pt-br.

PricingMapper.to_display(resultado) aplica format_brl em cada valor monetário
do dict retornado por PricingService.calcular, devolvendo strings prontas pro template.
"""
from __future__ import annotations

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper


class PricingMapper(BaseMapper):
    """Converte o resultado de PricingService.calcular em valores formatados para exibição."""

    # Chaves que representam valores monetários no resultado do PricingService
    _CHAVES_MONETARIAS = (
        "custo_material",
        "custo_energia",
        "custo_depreciacao",
        "custo_maoobra",
        "subtotal",
        "ajuste_falha",
        "custo_total",
        "preco_venda",
    )

    @classmethod
    def to_dict(cls, instance) -> dict:
        """Não utilizado — use to_display() para resultados de precificação."""
        return {}

    @classmethod
    def to_display(cls, resultado: dict) -> dict[str, str]:
        """Aplica format_brl em cada valor monetário do resultado.

        Devolve um dict com as mesmas chaves mas valores formatados em BRL
        (ex.: 'R$ 6,00', 'R$ 51,69'), prontos para o template.
        """
        return {
            chave: format_brl(resultado.get(chave))
            for chave in cls._CHAVES_MONETARIAS
        }
