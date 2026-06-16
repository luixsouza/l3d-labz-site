"""Mappers da calculadora — convertem dados de precificação e orçamentos em dicts formatados.

PricingMapper.to_display(resultado) — converte floats do PricingService em strings BRL.
OrcamentoMapper.to_public(orcamento) — converte Model -> dict SOMENTE com dados públicos.

SEGURANÇA (T-fma-01): OrcamentoMapper expõe APENAS os 7 campos da allowlist pública.
Jamais incluir custo_material, custo_energia, custo_depreciacao, custo_maoobra,
subtotal, ajuste_falha, custo_total, taxa_falha_pct ou margem_pct.
"""
from __future__ import annotations

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper

from .models import Orcamento


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


class OrcamentoMapper(BaseMapper[Orcamento]):
    """Converte Orcamento -> dict com SOMENTE os campos da allowlist pública (T-fma-01).

    Jamais incluir campos de custo interno — o model já não os possui, mas
    esta allowlist explícita garante que nenhuma refatoração futura vaze dados.
    """

    # Allowlist explícita — espelha a trava do pdf.py (linhas 6-18)
    _CAMPOS_PUBLICOS = (
        "cliente_nome",
        "peca_descricao",
        "quantidade",
        "prazo_entrega",
        "observacoes",
        "preco_venda",
        "total",
    )

    @classmethod
    def to_dict(cls, instance: Orcamento) -> dict:
        """Satisfaz o contrato BaseMapper — delega a to_public."""
        return cls.to_public(instance)

    @classmethod
    def to_public(cls, orcamento: Orcamento) -> dict:
        """Devolve APENAS os dados públicos formatados para o template.

        Campos retornados:
          token, cliente_nome, peca_descricao, quantidade, prazo_entrega,
          observacoes, preco_venda_display, total_display, created_at.
        """
        return {
            "token":             str(orcamento.token),
            "cliente_nome":      orcamento.cliente_nome,
            "peca_descricao":    orcamento.peca_descricao,
            "quantidade":        int(orcamento.quantidade),
            "prazo_entrega":     orcamento.prazo_entrega,
            "observacoes":       orcamento.observacoes,
            "preco_venda_display": format_brl(orcamento.preco_venda),
            "total_display":     format_brl(orcamento.total),
            "created_at":        orcamento.created_at,
        }
