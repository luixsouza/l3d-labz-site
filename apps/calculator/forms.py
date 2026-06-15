"""Formulários da calculadora de precificação — inputs de custo e dados do cliente.

CalcForm      — inputs de custo com presets de impressora/filamento e bandeira ANEEL.
OrcamentoForm — estende CalcForm com dados do cliente para o PDF de orçamento.

Padrão `to_calc_data()` espelhado de apps/orders/forms.py (to_order_data).
A soma tarifa_efetiva = tarifa_base + adicional_bandeira é feita aqui (to_calc_data),
mantendo a assinatura do PricingService inalterada (recebe um único tarifa_kwh).
"""
from __future__ import annotations

from django import forms

from .presets import (
    BANDEIRAS_ANEEL,
    BANDEIRA_VIGENTE_DEFAULT,
    bandeira_choices,
    filamento_choices,
    impressora_choices,
)


class CalcForm(forms.Form):
    """Inputs de custo para a calculadora de precificação de impressão 3D v2.

    Inclui selects de preset de impressora e filamento (UX de auto-preenchimento),
    além de tarifa_base + bandeira ANEEL no lugar do antigo campo tarifa_kwh único.
    Os presets NÃO entram em to_calc_data — são apenas UX; os valores reais usados
    são os campos numéricos editáveis.
    """

    # --- Preset de impressora (UX apenas — não vai a to_calc_data) ---
    impressora = forms.ChoiceField(
        label="Impressora",
        choices=impressora_choices,
        required=False,
        initial="manual",
        help_text="Selecione para auto-preencher potência, valor e vida útil.",
    )

    # --- Filamento ---
    # Preset de filamento (UX apenas)
    filamento = forms.ChoiceField(
        label="Material / filamento",
        choices=filamento_choices,
        required=False,
        initial="manual",
        help_text="Selecione para auto-preencher o preço/kg sugerido.",
    )
    peso_g = forms.FloatField(
        label="Peso do filamento (g)",
        min_value=0.1,
        help_text="Quantidade estimada de filamento consumido em gramas.",
    )
    preco_kg = forms.FloatField(
        label="Preço do filamento (R$/kg)",
        min_value=0.01,
        help_text="Preço por quilograma do filamento (ex.: PLA básico ≈ R$ 120/kg). O preset sugere um valor; informe o preço real da sua bobina.",
    )

    # --- Máquina (populados pelo preset de impressora, editáveis) ---
    potencia_w = forms.FloatField(
        label="Potência da impressora (W)",
        min_value=1.0,
        help_text="Potência ativa média durante impressão — não a potência da fonte (que é 2–3× maior). Use wattímetro para valor exato.",
    )
    valor_maquina = forms.FloatField(
        label="Valor da impressora (R$)",
        min_value=1.0,
        help_text="Custo de aquisição da impressora para cálculo de depreciação.",
    )
    vida_util_h = forms.FloatField(
        label="Vida útil estimada (h)",
        min_value=1.0,
        help_text="Horas de impressão até o fim da vida útil da máquina.",
    )

    # --- Tempo ---
    tempo_h = forms.FloatField(
        label="Tempo de impressão (h)",
        min_value=0.1,
        help_text="Tempo estimado de impressão em horas.",
    )

    # --- Energia: tarifa base + bandeira ANEEL (substituem o antigo tarifa_kwh) ---
    tarifa_base = forms.FloatField(
        label="Tarifa base da distribuidora (R$/kWh)",
        min_value=0.01,
        help_text=(
            "Tarifa residencial da sua distribuidora em R$/kWh "
            "(média BR 2025 ≈ R$ 0,95). Veja na sua conta de luz."
        ),
    )
    bandeira = forms.ChoiceField(
        label="Bandeira tarifária ANEEL",
        choices=bandeira_choices,
        initial=BANDEIRA_VIGENTE_DEFAULT,
        help_text="O adicional da bandeira é somado à tarifa base para obter a tarifa efetiva.",
    )

    # --- Trabalho ---
    custo_maoobra = forms.FloatField(
        label="Custo de mão de obra (R$)",
        min_value=0.0,
        help_text="Valor fixo de mão de obra para a peça (preparação, pós-processamento etc.).",
    )

    # --- Margem e risco ---
    taxa_falha_pct = forms.FloatField(
        label="Taxa de falha / reimpressão (%)",
        min_value=0.0,
        max_value=100.0,
        help_text="Percentual sobre o custo para cobrir peças falhas ou reimpressões.",
    )
    margem_pct = forms.FloatField(
        label="Margem de lucro (%)",
        min_value=0.0,
        help_text="Percentual de margem aplicado sobre o custo total para obter o preço de venda.",
    )

    def to_calc_data(self) -> dict:
        """Converte o form validado no dict que PricingService.calcular espera.

        Calcula a tarifa efetiva somando o adicional da bandeira ANEEL à tarifa base
        ANTES de chamar o serviço — a assinatura do PricingService permanece inalterada
        (recebe um único 'tarifa_kwh').
        Os campos de preset (impressora/filamento) NÃO entram aqui — são apenas UX.
        """
        c = self.cleaned_data
        # --- soma da bandeira (decisão arquitetural: feita no form, não no serviço) ---
        adicional = BANDEIRAS_ANEEL[c["bandeira"]]["adicional_kwh"]
        tarifa_kwh = c["tarifa_base"] + adicional
        return {
            "peso_g":         c["peso_g"],
            "preco_kg":       c["preco_kg"],
            "potencia_w":     c["potencia_w"],
            "tempo_h":        c["tempo_h"],
            "tarifa_kwh":     tarifa_kwh,       # tarifa efetiva = base + adicional_bandeira
            "valor_maquina":  c["valor_maquina"],
            "vida_util_h":    c["vida_util_h"],
            "custo_maoobra":  c["custo_maoobra"],
            "taxa_falha_pct": c["taxa_falha_pct"],
            "margem_pct":     c["margem_pct"],
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
