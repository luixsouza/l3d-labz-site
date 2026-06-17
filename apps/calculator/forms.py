"""Formulários da calculadora de precificação — inputs de custo e dados do cliente.

CalcForm      — inputs de custo (modelo enxuto: material, energia, mão de obra, custos fixos, margem).
OrcamentoForm — estende CalcForm com dados do cliente para o PDF de orçamento.

Padrão `to_calc_data()` espelhado de apps/orders/forms.py (to_order_data).
O campo valor_kwh vai direto ao serviço (sem soma de bandeira aqui — o usuário
escolhe o kWh total via chips de bandeira ou digita manualmente).
"""
from __future__ import annotations

from django import forms

from .presets import filamento_choices


class CalcForm(forms.Form):
    """Inputs de custo para a calculadora de precificação de impressão 3D (modelo enxuto).

    Fórmula (decisão D-01 enxuto):
      custo_material  = (peso_g / 1000) * preco_kg
      custo_energia   = (potencia_w / 1000) * tempo_h * valor_kwh
      subtotal        = custo_material + custo_energia + custo_maoobra + custos_fixos
      preco_venda     = subtotal * (1 + margem_pct / 100)

    Os chips de consumo e de bandeira NÃO entram em to_calc_data — são apenas UX
    que preenchem potencia_w e valor_kwh no client antes do submit.
    """

    # --- Preset de filamento (UX apenas — não vai a to_calc_data) ---
    filamento = forms.ChoiceField(
        label="Material de referência",
        choices=filamento_choices,
        required=False,
        initial="pla",
        help_text="Selecione para puxar o preço/kg de referência L3D.",
    )

    # --- Filamento ---
    peso_g = forms.FloatField(
        label="Quantidade Utilizada (g)",
        min_value=0.1,
        help_text="Consulte o fatiador para saber a gramagem.",
    )
    preco_kg = forms.FloatField(
        label="Preço do Filamento (R$/kg)",
        min_value=0.01,
        help_text="Preço por quilograma do filamento. Use 'Puxar preço do site' para o valor L3D.",
    )

    # --- Energia ---
    potencia_w = forms.FloatField(
        label="Consumo da Impressora (W)",
        min_value=1.0,
        help_text="Potência média durante impressão (não a da fonte). Use os chips abaixo.",
    )
    tempo_h = forms.FloatField(
        label="Tempo de Impressão (horas)",
        min_value=0.1,
        help_text="Tempo estimado de impressão em horas.",
    )
    valor_kwh = forms.FloatField(
        label="Valor do kWh (R$)",
        min_value=0.01,
        initial=0.95,
        help_text="Tarifa do kWh da sua distribuidora com bandeira inclusa. Use os chips de bandeira.",
    )

    # --- Opcionais ---
    custo_maoobra = forms.FloatField(
        label="Mão de Obra (R$)",
        min_value=0.0,
        initial=0.0,
        required=False,
        help_text="Valor fixo por peça (preparação, acabamento, etc.).",
    )
    custos_fixos = forms.FloatField(
        label="Custos Fixos (R$)",
        min_value=0.0,
        initial=0.0,
        required=False,
        help_text="Desgaste da impressora, acabamento, etc.",
    )
    margem_pct = forms.FloatField(
        label="Margem de Lucro (%)",
        min_value=0.0,
        initial=100.0,
        help_text="Percentual de margem sobre o subtotal para obter o preço de venda.",
    )

    def to_calc_data(self) -> dict:
        """Converte o form validado no dict que PricingService.calcular espera.

        Campos retornados: peso_g, preco_kg, potencia_w, tempo_h, valor_kwh,
        custo_maoobra, custos_fixos, margem_pct.
        O campo filamento NÃO entra — é apenas UX.
        """
        c = self.cleaned_data
        return {
            "peso_g":        c["peso_g"],
            "preco_kg":      c["preco_kg"],
            "potencia_w":    c["potencia_w"],
            "tempo_h":       c["tempo_h"],
            "valor_kwh":     c["valor_kwh"],
            "custo_maoobra": c.get("custo_maoobra") or 0.0,
            "custos_fixos":  c.get("custos_fixos") or 0.0,
            "margem_pct":    c["margem_pct"],
        }


class OrcamentoForm(CalcForm):
    """Estende CalcForm com os dados do cliente para emissão do PDF de orçamento.

    Campos adicionais: cliente, peça, quantidade, prazo, observações.
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
