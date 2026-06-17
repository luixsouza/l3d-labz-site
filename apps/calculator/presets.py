"""Presets da calculadora de precificação 3D — filamentos, chips de consumo e bandeiras de kWh.

Vigência dos dados: 2026-06-17.
Fonte dos chips de consumo: pesquisa 2026-06 (potências médias de impressão ativas, não pico).
Fonte do BANDEIRA_KWH: tarifa base residencial BR 2025 ≈ R$0,95/kWh (ANEEL); adicionais
  Verde: sem adicional (bandeira verde — cenário hídrico favorável).
  Amarela: +R$0,02 (aproximação do adicional ANEEL vigente, atualizar mensalmente).
  Vermelha: +R$0,07 (média entre P1 R$0,04463 e P2 R$0,07877 — simplificação para UX).
"""
from __future__ import annotations

import json

# ---- Filamentos FDM -----------------------------------------------------------------
# Preços são sugestões iniciais (preco_kg_default) — o usuário deve informar o preço real
# da bobina comprada. Densidades baseadas em fichas técnicas de fabricantes (literatura padrão).
FILAMENTOS: dict[str, dict] = {
    "pla": {
        "label": "PLA",
        "densidade_g_cm3": 1.24,
        "preco_kg_default": 120.0,
        "bico_c": "190–220",
        "mesa_c": "50–60",
    },
    "pla_plus": {
        "label": "PLA+",
        "densidade_g_cm3": 1.24,
        "preco_kg_default": 130.0,
        "bico_c": "200–230",
        "mesa_c": "50–65",
    },
    "petg": {
        "label": "PETG",
        "densidade_g_cm3": 1.27,
        "preco_kg_default": 150.0,
        "bico_c": "230–250",
        "mesa_c": "70–90",
    },
    "abs": {
        "label": "ABS",
        "densidade_g_cm3": 1.05,
        "preco_kg_default": 110.0,
        "bico_c": "230–250",
        "mesa_c": "90–110",
    },
    "asa": {
        "label": "ASA",
        "densidade_g_cm3": 1.07,
        "preco_kg_default": 190.0,
        "bico_c": "240–260",
        "mesa_c": "90–110",
    },
    "tpu": {
        "label": "TPU 95A (flexível)",
        "densidade_g_cm3": 1.21,
        "preco_kg_default": 150.0,
        "bico_c": "220–240",
        "mesa_c": "40–60",
    },
    "nylon": {
        "label": "Nylon / PA6",
        "densidade_g_cm3": 1.13,
        "preco_kg_default": 280.0,
        "bico_c": "240–270",
        "mesa_c": "70–90",
    },
    "pc": {
        "label": "PC (Policarbonato)",
        "densidade_g_cm3": 1.20,
        "preco_kg_default": 230.0,
        "bico_c": "260–300",
        "mesa_c": "100–120",
    },
    "pla_cf": {
        "label": "PLA-CF (fibra de carbono)",
        "densidade_g_cm3": 1.29,
        "preco_kg_default": 200.0,
        "bico_c": "200–230",
        "mesa_c": "50–65",
    },
    "petg_cf": {
        "label": "PETG-CF (fibra de carbono)",
        "densidade_g_cm3": 1.30,
        "preco_kg_default": 220.0,
        "bico_c": "240–260",
        "mesa_c": "70–90",
    },
    # Entrada manual — mantida sempre por último na UI
    "manual": {
        "label": "Outro / manual",
        "densidade_g_cm3": 0,
        "preco_kg_default": 0,
        "bico_c": "",
        "mesa_c": "",
    },
}

# ---- Chips de consumo de impressora (UX: preenchem potencia_w no client) -----------
# Fonte: medições médias de impressão ativa por wattímetro. NÃO é a potência da fonte.
# Bambu A1 ~200W (mockup): estimativa de uso contínuo com cama aquecida.
# Bambu X1C ~350W: potência mais alta quando câmara aquecida + multicolor.
CONSUMO_CHIPS: list[dict] = [
    {"label": "Ender 3 (~120W)", "w": 120},
    {"label": "Bambu A1 (~200W)", "w": 200},
    {"label": "Bambu X1C (~350W)", "w": 350},
]

# ---- Chips de bandeira tarifária (UX: preenchem valor_kwh no client) ---------------
# Tarifa base BR 2025 ≈ R$0,95/kWh. Adicionais ANEEL simplificados para UX.
# Para cálculo preciso, o usuário deve ajustar o campo Valor do kWh manualmente.
BANDEIRA_KWH: dict[str, float] = {
    "verde":     0.95,   # sem adicional
    "amarela":   0.97,   # base + adicional amarela (aprox.)
    "vermelha":  1.02,   # base + adicional vermelha média (P1+P2)/2 aprox.
}

# ---- Legados (mantidos para compatibilidade com possíveis referências externas) ----
# IMPRESSORAS e BANDEIRAS_ANEEL removidos do JSON do JS (calculator.js novo usa
# filamentos/consumo_chips/bandeira_kwh). Mantidos aqui como fallback de leitura.
IMPRESSORAS: dict[str, dict] = {}
BANDEIRAS_ANEEL: dict[str, dict] = {}
BANDEIRA_VIGENTE_DEFAULT = "verde"


# ---- Helpers de choices para os forms -----------------------------------------------

def filamento_choices() -> list[tuple[str, str]]:
    """Retorna lista de (value, label) para o ChoiceField de filamento.

    A entrada 'manual' (Outro / manual) é sempre a última da lista.
    """
    choices = [
        (key, data["label"])
        for key, data in FILAMENTOS.items()
        if key != "manual"
    ]
    choices.append(("manual", FILAMENTOS["manual"]["label"]))
    return choices


def presets_json() -> dict:
    """Serializa os presets enxutos para injeção via json_script no template.

    Retorna dict serializável com 'filamentos', 'consumo_chips' e 'bandeira_kwh' —
    sem impressoras/bandeiras antigas (removidas do modelo enxuto).
    """
    return {
        "filamentos":    FILAMENTOS,
        "consumo_chips": CONSUMO_CHIPS,
        "bandeira_kwh":  BANDEIRA_KWH,
    }
