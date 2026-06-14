"""Serviço de precificação de impressão 3D — fonte única da verdade das fórmulas de custo.

Modelo de custo COMPLETO (decisão D-01):
  - custo_material  = (peso_g / 1000) * preco_kg
  - custo_energia   = (potencia_w / 1000) * tempo_h * tarifa_kwh
  - custo_depreciacao = (valor_maquina / vida_util_h) * tempo_h
  - custo_maoobra   = valor fixo informado (passthrough)
  - subtotal        = soma dos quatro acima
  - ajuste_falha    = subtotal * (taxa_falha_pct / 100)
  - custo_total     = subtotal + ajuste_falha
  - preco_venda     = custo_total * (1 + margem_pct / 100)

App stateless (sem models): todos os cálculos vivem aqui.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from apps.core.layers import BaseService


@dataclass(frozen=True)
class CustoDefaults:
    """Valores padrão de custo — editáveis num único lugar (decisão D-05).

    Impressoras de referência:
      - Creality Ender 3: ~110 W de potência ativa
      - Prusa i3 MK3S+: ~180 W de potência ativa
    """

    tarifa_kwh: float = 0.95       # R$/kWh (tarifa residencial típica BR 2025)
    margem_pct: float = 150.0      # margem sobre o custo total (%)
    taxa_falha_pct: float = 10.0   # ajuste para taxa de falha/reimpressão (%)
    potencia_w: float = 110.0      # watts (Ender 3; Prusa i3 MK3S+ ≈ 180 W)
    valor_maquina: float = 2000.0  # custo da impressora (R$)
    vida_util_h: float = 2000.0    # horas úteis estimadas até o fim da vida


_DEFAULTS = CustoDefaults()

_DOIS = Decimal("0.01")  # quantizador para arredondar a 2 casas decimais


def _d(value: float | int) -> Decimal:
    """Converte para Decimal para cálculos monetários precisos."""
    return Decimal(str(value))


class PricingService(BaseService):
    """Cálculo de preço de impressão 3D — stateless."""

    @staticmethod
    def calcular(
        *,
        peso_g: float,
        preco_kg: float,
        potencia_w: float = _DEFAULTS.potencia_w,
        tempo_h: float,
        tarifa_kwh: float = _DEFAULTS.tarifa_kwh,
        valor_maquina: float = _DEFAULTS.valor_maquina,
        vida_util_h: float = _DEFAULTS.vida_util_h,
        custo_maoobra: float,
        taxa_falha_pct: float = _DEFAULTS.taxa_falha_pct,
        margem_pct: float = _DEFAULTS.margem_pct,
    ) -> dict[str, float]:
        """Calcula o preço de venda e o detalhamento completo de custos.

        Devolve um dict com 8 chaves (valores float arredondados a 2 casas):
          custo_material, custo_energia, custo_depreciacao, custo_maoobra,
          subtotal, ajuste_falha, custo_total, preco_venda.
        """
        # --- material ---
        custo_material = (_d(peso_g) / _d(1000)) * _d(preco_kg)

        # --- energia elétrica ---
        custo_energia = (_d(potencia_w) / _d(1000)) * _d(tempo_h) * _d(tarifa_kwh)

        # --- depreciação da máquina ---
        custo_depreciacao = (_d(valor_maquina) / _d(vida_util_h)) * _d(tempo_h)

        # --- mão de obra (passthrough do valor informado) ---
        custo_maoobra_d = _d(custo_maoobra)

        # --- subtotal ---
        subtotal = custo_material + custo_energia + custo_depreciacao + custo_maoobra_d

        # --- ajuste de falha/reimpressão ---
        ajuste_falha = subtotal * (_d(taxa_falha_pct) / _d(100))
        custo_total = subtotal + ajuste_falha

        # --- preço de venda com margem ---
        preco_venda = custo_total * (_d(1) + _d(margem_pct) / _d(100))

        def _arredondar(v: Decimal) -> float:
            return float(v.quantize(_DOIS, rounding=ROUND_HALF_UP))

        return {
            "custo_material":    _arredondar(custo_material),
            "custo_energia":     _arredondar(custo_energia),
            "custo_depreciacao": _arredondar(custo_depreciacao),
            "custo_maoobra":     _arredondar(custo_maoobra_d),
            "subtotal":          _arredondar(subtotal),
            "ajuste_falha":      _arredondar(ajuste_falha),
            "custo_total":       _arredondar(custo_total),
            "preco_venda":       _arredondar(preco_venda),
        }
