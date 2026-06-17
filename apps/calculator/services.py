"""Serviços da calculadora de precificação de impressão 3D.

PricingService — fonte única da verdade das fórmulas de custo (decisão D-01 enxuto):
  - custo_material  = (peso_g / 1000) * preco_kg
  - custo_energia   = (potencia_w / 1000) * tempo_h * valor_kwh
  - custo_maoobra   = valor fixo informado (passthrough)
  - custos_fixos    = valor fixo informado (passthrough)
  - subtotal        = custo_material + custo_energia + custo_maoobra + custos_fixos
  - preco_venda     = subtotal * (1 + margem_pct / 100)

  REMOVIDOS: custo_depreciacao (valor_maquina/vida_util_h), ajuste_falha (taxa_falha_pct),
  custo_total. Simplificação aprovada pelo usuário (mockup 2026-06-17).

OrcamentoService — persistência dos dados PÚBLICOS do orçamento (T-mrl-01):
  Único ponto de escrita no banco; recebe apenas os 7 campos públicos,
  NUNCA custos internos (custo_maoobra, custos_fixos, margem_pct não entram no banco).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from apps.core.layers import BaseService

from .models import Orcamento


@dataclass(frozen=True)
class CustoDefaults:
    """Valores padrão de custo — editáveis num único lugar (decisão D-05 enxuto).

    Modelo enxuto: sem valor_maquina, vida_util_h, taxa_falha_pct.
    """

    valor_kwh: float = 0.95       # R$/kWh (tarifa residencial típica BR 2025, bandeira verde)
    margem_pct: float = 100.0     # margem sobre o subtotal (%)
    potencia_w: float = 200.0     # watts (Bambu A1 — impressora de referência do mockup)


_DEFAULTS = CustoDefaults()

_DOIS = Decimal("0.01")  # quantizador para arredondar a 2 casas decimais


def _d(value: float | int) -> Decimal:
    """Converte para Decimal para cálculos monetários precisos."""
    return Decimal(str(value))


class PricingService(BaseService):
    """Cálculo de preço de impressão 3D — stateless (modelo enxuto)."""

    @staticmethod
    def calcular(
        *,
        peso_g: float,
        preco_kg: float,
        potencia_w: float = _DEFAULTS.potencia_w,
        tempo_h: float,
        valor_kwh: float = _DEFAULTS.valor_kwh,
        custo_maoobra: float,
        custos_fixos: float = 0.0,
        margem_pct: float = _DEFAULTS.margem_pct,
    ) -> dict[str, float]:
        """Calcula o preço de venda e o detalhamento enxuto de custos.

        Devolve um dict com EXATAMENTE 6 chaves (valores float arredondados a 2 casas):
          custo_material, custo_energia, custo_maoobra, custos_fixos, subtotal, preco_venda.
        """
        # --- material ---
        custo_material = (_d(peso_g) / _d(1000)) * _d(preco_kg)

        # --- energia elétrica ---
        custo_energia = (_d(potencia_w) / _d(1000)) * _d(tempo_h) * _d(valor_kwh)

        # --- mão de obra (passthrough do valor informado) ---
        custo_maoobra_d = _d(custo_maoobra)

        # --- custos fixos (passthrough do valor informado) ---
        custos_fixos_d = _d(custos_fixos)

        # --- subtotal ---
        subtotal = custo_material + custo_energia + custo_maoobra_d + custos_fixos_d

        # --- preço de venda com margem ---
        preco_venda = subtotal * (_d(1) + _d(margem_pct) / _d(100))

        def _arredondar(v: Decimal) -> float:
            return float(v.quantize(_DOIS, rounding=ROUND_HALF_UP))

        return {
            "custo_material": _arredondar(custo_material),
            "custo_energia":  _arredondar(custo_energia),
            "custo_maoobra":  _arredondar(custo_maoobra_d),
            "custos_fixos":   _arredondar(custos_fixos_d),
            "subtotal":       _arredondar(subtotal),
            "preco_venda":    _arredondar(preco_venda),
        }


class OrcamentoService(BaseService):
    """Persistência dos dados PÚBLICOS do orçamento — única camada que escreve no banco.

    SEGURANÇA (T-mrl-01): recebe SOMENTE os 7 campos públicos (keyword-only).
    Jamais aceitar custo_material, custo_energia, custo_maoobra, custos_fixos,
    subtotal, margem_pct — esses dados NÃO entram no banco.
    """

    @staticmethod
    @transaction.atomic
    def criar(
        *,
        cliente_nome: str,
        peca_descricao: str,
        quantidade: int,
        prazo_entrega: str,
        observacoes: str,
        preco_venda,
        total,
    ) -> Orcamento:
        """Persiste um novo orçamento com os dados públicos e retorna a instância.

        preco_venda e total podem ser float, str ou Decimal — convertidos aqui.
        """
        return Orcamento.objects.create(
            cliente_nome=cliente_nome,
            peca_descricao=peca_descricao,
            quantidade=int(quantidade),
            prazo_entrega=prazo_entrega,
            observacoes=observacoes or "",
            preco_venda=Decimal(str(preco_venda)),
            total=Decimal(str(total)),
        )
