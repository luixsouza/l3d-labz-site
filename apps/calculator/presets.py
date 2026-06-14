"""Presets genéricos da calculadora de precificação 3D — impressoras, filamentos e bandeiras ANEEL.

Vigência dos dados: 2026-06-14.
Fonte das bandeiras ANEEL: Jornal de Brasília / ANEEL (junho 2025).
Nota de potência: os valores de 'potencia_w' são médias de impressão ativas medidas por
wattímetro — NÃO a potência de pico da fonte (que é 2–3x maior).

Atualizar BANDEIRA_VIGENTE_DEFAULT mensalmente conforme resolução ANEEL.
"""
from __future__ import annotations

import json

# ---- Impressoras FDM ----------------------------------------------------------------
# Fonte: pesquisa 2026-06-14 — valores de potência são médias de impressão, NÃO pico da fonte.
# Marcados como "# estimado" quando não há medição publicada por wattímetro.
IMPRESSORAS: dict[str, dict] = {
    "ender3_v3_se": {
        "label": "Creality Ender 3 V3 SE",
        "potencia_w": 100,       # estimado
        "valor_maquina": 1499,
        "vida_util_h": 2000,
    },
    "ender3_v3_ke": {
        "label": "Creality Ender 3 V3 KE",
        "potencia_w": 120,       # estimado
        "valor_maquina": 2199,
        "vida_util_h": 2000,
    },
    "ender3_v3": {
        "label": "Creality Ender 3 V3",
        "potencia_w": 130,       # estimado
        "valor_maquina": 2339,
        "vida_util_h": 2000,
    },
    "k1": {
        "label": "Creality K1",
        "potencia_w": 100,
        "valor_maquina": 4130,
        "vida_util_h": 3000,
    },
    "k1_max": {
        "label": "Creality K1 Max",
        "potencia_w": 150,       # estimado
        "valor_maquina": 9499,
        "vida_util_h": 3000,
    },
    "bambu_a1_mini": {
        "label": "Bambu Lab A1 Mini",
        "potencia_w": 90,
        "valor_maquina": 2319,
        "vida_util_h": 3000,
    },
    "bambu_a1": {
        "label": "Bambu Lab A1",
        "potencia_w": 110,       # estimado
        "valor_maquina": 3529,
        "vida_util_h": 3000,
    },
    "bambu_p1s": {
        "label": "Bambu Lab P1S",
        "potencia_w": 120,
        "valor_maquina": 7789,
        "vida_util_h": 4000,
    },
    "bambu_x1c": {
        "label": "Bambu Lab X1 Carbon",
        "potencia_w": 120,
        "valor_maquina": 15463,
        "vida_util_h": 4000,
    },
    "kobra3_combo": {
        "label": "Anycubic Kobra 3 Combo",
        "potencia_w": 140,       # estimado
        "valor_maquina": 4000,   # estimado
        "vida_util_h": 3000,
    },
    "neptune4": {
        "label": "Elegoo Neptune 4",
        "potencia_w": 160,
        "valor_maquina": 2000,   # estimado (esgotado em lojas)
        "vida_util_h": 2000,
    },
    "neptune4_pro": {
        "label": "Elegoo Neptune 4 Pro",
        "potencia_w": 150,       # estimado
        "valor_maquina": 2800,
        "vida_util_h": 2000,
    },
    "prusa_mk4s": {
        "label": "Prusa MK4S",
        "potencia_w": 120,
        "valor_maquina": 5500,   # estimado (importado ~USD 925)
        "vida_util_h": 5000,
    },
    "prusa_mini_plus": {
        "label": "Prusa MINI+",
        "potencia_w": 80,
        "valor_maquina": 3200,   # estimado (importado)
        "vida_util_h": 4000,
    },
    # Entrada manual — mantida sempre por último na UI
    "manual": {
        "label": "Outra / manual",
        "potencia_w": 0,
        "valor_maquina": 0,
        "vida_util_h": 0,
    },
}

# ---- Bandeiras ANEEL ----------------------------------------------------------------
# Fonte: Jornal de Brasília / ANEEL — vigência jun/2025; atualizar mensalmente.
# O adicional se SOMA à tarifa base: tarifa_efetiva = tarifa_base + adicional_kwh.
BANDEIRAS_ANEEL: dict[str, dict] = {
    "verde": {
        "label": "Verde (sem adicional)",
        "adicional_kwh": 0.0,
    },
    "amarela": {
        "label": "Amarela (+R$ 0,01885/kWh)",
        "adicional_kwh": 0.01885,
    },
    "vermelha1": {
        "label": "Vermelha Patamar 1 (+R$ 0,04463/kWh)",
        "adicional_kwh": 0.04463,
    },
    "vermelha2": {
        "label": "Vermelha Patamar 2 (+R$ 0,07877/kWh)",
        "adicional_kwh": 0.07877,
    },
}

# Bandeira vigente por padrão — atualizar mensalmente conforme ANEEL.
# Última atualização: 2026-06-14. Vigente: Amarela (mai–jun 2025).
BANDEIRA_VIGENTE_DEFAULT = "amarela"

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


# ---- Helpers de choices para os forms -----------------------------------------------

def impressora_choices() -> list[tuple[str, str]]:
    """Retorna lista de (value, label) para o ChoiceField de impressora.

    A entrada 'manual' (Outra / manual) é sempre a última da lista.
    """
    choices = [
        (key, data["label"])
        for key, data in IMPRESSORAS.items()
        if key != "manual"
    ]
    choices.append(("manual", IMPRESSORAS["manual"]["label"]))
    return choices


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


def bandeira_choices() -> list[tuple[str, str]]:
    """Retorna lista de (value, label) para o ChoiceField de bandeira ANEEL.

    'verde' (sem adicional) aparece primeiro.
    """
    ordem = ["verde", "amarela", "vermelha1", "vermelha2"]
    return [(key, BANDEIRAS_ANEEL[key]["label"]) for key in ordem if key in BANDEIRAS_ANEEL]


def presets_json() -> dict:
    """Serializa os presets para injeção via json_script no template.

    Retorna dict serializável com 'impressoras', 'filamentos' e 'bandeiras' —
    sem duplicar números literais no JS.
    """
    return {
        "impressoras": IMPRESSORAS,
        "filamentos": FILAMENTOS,
        "bandeiras": BANDEIRAS_ANEEL,
    }
