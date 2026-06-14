"""Formulários da calculadora de precificação — inputs de custo e dados do cliente.

CalcForm    — inputs de custo para a calculadora pública e de orçamento.
OrcamentoForm — estende CalcForm com dados do cliente para o PDF de orçamento.

Padrão `to_calc_data()` espelhado de apps/orders/forms.py (to_order_data).
"""
from __future__ import annotations

from django import forms

from .services import CustoDefaults

_DEF = CustoDefaults()


class CalcForm(forms.Form):
    """Inputs de custo para a calculadora de precificação de impressão 3D."""

    # --- Filamento ---
    peso_g = forms.FloatField(
        label="Peso do filamento (g)",
        initial=50.0,
        min_value=0.1,
        help_text="Quantidade estimada de filamento consumido em gramas.",
    )
    preco_kg = forms.FloatField(
        label="Preço do filamento (R$/kg)",
        initial=120.0,
        min_value=0.01,
        help_text="Preço por quilograma do filamento (ex.: PLA básico ≈ R$120/kg).",
    )

    # --- Energia ---
    potencia_w = forms.FloatField(
        label="Potência da impressora (W)",
        initial=_DEF.potencia_w,
        min_value=1.0,
        help_text="Potência ativa da impressora em watts (Ender 3 ≈ 110 W; Prusa i3 MK3S+ ≈ 180 W).",
    )
    tempo_h = forms.FloatField(
        label="Tempo de impressão (h)",
        initial=4.0,
        min_value=0.1,
        help_text="Tempo estimado de impressão em horas.",
    )
    tarifa_kwh = forms.FloatField(
        label="Tarifa de energia (R$/kWh)",
        initial=_DEF.tarifa_kwh,
        min_value=0.01,
        help_text="Tarifa de energia elétrica em R$ por kWh (média residencial BR 2025 ≈ R$0,95).",
    )

    # --- Máquina ---
    valor_maquina = forms.FloatField(
        label="Valor da impressora (R$)",
        initial=_DEF.valor_maquina,
        min_value=1.0,
        help_text="Custo de aquisição da impressora para cálculo de depreciação.",
    )
    vida_util_h = forms.FloatField(
        label="Vida útil estimada (h)",
        initial=_DEF.vida_util_h,
        min_value=1.0,
        help_text="Horas de impressão até o fim da vida útil da máquina.",
    )

    # --- Trabalho ---
    custo_maoobra = forms.FloatField(
        label="Custo de mão de obra (R$)",
        initial=10.0,
        min_value=0.0,
        help_text="Valor fixo de mão de obra para a peça (preparação, pós-processamento etc.).",
    )

    # --- Margem e risco ---
    taxa_falha_pct = forms.FloatField(
        label="Taxa de falha / reimpressão (%)",
        initial=_DEF.taxa_falha_pct,
        min_value=0.0,
        max_value=100.0,
        help_text="Percentual sobre o custo para cobrir peças falhas ou reimpressões.",
    )
    margem_pct = forms.FloatField(
        label="Margem de lucro (%)",
        initial=_DEF.margem_pct,
        min_value=0.0,
        help_text="Percentual de margem aplicado sobre o custo total para obter o preço de venda.",
    )

    def to_calc_data(self) -> dict:
        """Converte o form validado no dict que PricingService.calcular espera."""
        c = self.cleaned_data
        return {
            "peso_g":       c["peso_g"],
            "preco_kg":     c["preco_kg"],
            "potencia_w":   c["potencia_w"],
            "tempo_h":      c["tempo_h"],
            "tarifa_kwh":   c["tarifa_kwh"],
            "valor_maquina": c["valor_maquina"],
            "vida_util_h":  c["vida_util_h"],
            "custo_maoobra": c["custo_maoobra"],
            "taxa_falha_pct": c["taxa_falha_pct"],
            "margem_pct":   c["margem_pct"],
        }


class OrcamentoForm(CalcForm):
    """Estende CalcForm com os dados do cliente para emissão do PDF de orçamento.

    Campos adicionais (decisão D-03): cliente, peça, quantidade, prazo, observações.
    """

    # --- Dados do cliente ---
    cliente_nome = forms.CharField(
        label="Nome do cliente",
        max_length=120,
        help_text="Nome completo do cliente para o orçamento.",
    )
    peca_descricao = forms.CharField(
        label="Descrição da peça",
        max_length=240,
        help_text="Nome ou descrição da peça a ser impressa.",
    )
    quantidade = forms.IntegerField(
        label="Quantidade",
        initial=1,
        min_value=1,
        help_text="Número de unidades a produzir.",
    )
    prazo_entrega = forms.CharField(
        label="Prazo de entrega",
        max_length=80,
        help_text="Ex.: 3 dias úteis, 1 semana.",
    )
    observacoes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Informações adicionais para o cliente (opcional).",
    )
