# Pesquisa: Calculadora de Precificação 3D v2 — Presets Genéricos

**Data:** 2026-06-14
**Domínio:** FDM pricing calculator — dados de preset (impressoras, bandeiras ANEEL, filamentos)
**Confiança geral:** MEDIUM (potência média = mix de medições reais + estimativas; preços BR mudam rápido)

---

## 1. Impressoras FDM — Tabela de Presets

> Potência ATIVA MÉDIA = média real medida por wattímetro durante impressão contínua (não pico de aquecimento).
> Valores de potência máxima da fonte são sistematicamente mais altos (2–3×) que a média real de impressão.

| Modelo | Potência média (W) | Fonte / Nota | Valor típico BR (R$) | Vida útil est. (h) |
|--------|--------------------|--------------|----------------------|--------------------|
| Creality Ender 3 (original/V2) | 120 | [CITED: 3dsolved.com / 3dprintbeast.com] medição wattímetro 200°C / mesa 60°C | ~R$ 800–1.200 (descontinuado) | 1.500 |
| Creality Ender 3 V3 SE | 100 (estimado) | [ASSUMED] sem medição publicada para SE; fonte 350W, mesa menor que original → estimativa conservadora | R$ 1.499 [CITED: MercadoLivre BR] | 2.000 |
| Creality Ender 3 V3 KE | 120 (estimado) | [ASSUMED] fonte 350W, velocidade maior implica motores mais ativos; sem medição wattímetro publicada | R$ 2.199 [CITED: slim3d.com.br] | 2.000 |
| Creality Ender 3 V3 | 130 (estimado) | [ASSUMED] fonte 350W, CoreXY; sem medição wattímetro publicada; estimativa por analogia a K1 | R$ 2.339 [CITED: MercadoLivre BR] | 2.000 |
| Creality K1 | 100 | [CITED: pea3d.com / 3dprintbeginner.com] média estável pós-aquecimento ~100W, picos até 295W | R$ 4.130 [CITED: slim3d.com.br] | 3.000 |
| Creality K1 Max | 150 (estimado) | [ASSUMED] fonte 1.000W máx, mesa maior 300×300; média estimada por analogia ao K1 + overhead da cama extra | R$ 9.499 [CITED: slim3d.com.br] | 3.000 |
| Bambu Lab A1 Mini | 90 | [CITED: Bambu Lab Community Forum / call-3d.com] ~0,09 kWh/h medido | R$ 2.319 [CITED: gtmax3d.com.br] | 3.000 |
| Bambu Lab A1 | 110 (estimado) | [ASSUMED] maior que A1 Mini; intervalo documentado 50–200W, estimativa central | R$ 3.529 [CITED: gtmax3d.com.br] | 3.000 |
| Bambu Lab P1S | 120 | [CITED: Bambu Lab Forum / WebSearch] ~0,1 kWh/h medido = 100W; range forum: 105–145W → média 120W | R$ 7.789 [CITED: MercadoLivre BR] | 4.000 |
| Bambu Lab X1 Carbon | 120 | [CITED: Bambu Lab Forum thread #4180] medição wattímetro: 103–135W durante impressão (média ~120W) | R$ 15.463 [CITED: MercadoLivre BR] | 4.000 |
| Anycubic Kobra 2 | 120 (estimado) | [ASSUMED] fonte 400W; sem medição wattímetro publicada; estimativa por analogia a Ender 3 V3 | R$ 1.200–1.800 (geração anterior) | 2.000 |
| Anycubic Kobra 3 Combo | 140 (estimado) | [ASSUMED] 600mm/s, fonte maior; sem medição wattímetro publicada | R$ 3.500–4.500 (estimado) | 3.000 |
| Elegoo Neptune 4 | 160 | [CITED: igorslab.de review] medição real: 160–190W imprimindo PLA a velocidade normal | R$ 1.800–2.200 (estimado) | 2.000 |
| Elegoo Neptune 4 Pro | 150 (estimado) | [CITED: thephonograph.net] 124–192W no modo Sport; média estimada 150W | R$ 2.800 [CITED: bestlayer3d.com.br] | 2.000 |
| Prusa MK4S | 120 | [CITED: prusa3d.com specs] 80W PLA / 120W ABS/PETG oficial; confirmado por xargas.eu (medição PETG: 160W, PLA: ~90W) → preset médio 120W | ~R$ 5.000–6.000 (importado, USD 925) | 5.000 |
| Prusa MINI+ | 80 | [CITED: Prusa Forum] 60–90W em impressão normal; fonte 150W; média estimada 80W | ~R$ 3.000–3.500 (importado) | 4.000 |

### Notas de implementação (Python dict)

```python
# apps/calculator/presets.py
# Fonte: pesquisa 2026-06-14 — valores de potência são médias de impressão, NÃO pico da fonte
IMPRESSORAS = {
    "ender3_v3_se": {
        "label": "Creality Ender 3 V3 SE",
        "potencia_w": 100,      # estimado
        "valor_maquina": 1499,
        "vida_util_h": 2000,
    },
    "ender3_v3_ke": {
        "label": "Creality Ender 3 V3 KE",
        "potencia_w": 120,      # estimado
        "valor_maquina": 2199,
        "vida_util_h": 2000,
    },
    "ender3_v3": {
        "label": "Creality Ender 3 V3",
        "potencia_w": 130,      # estimado
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
        "potencia_w": 150,      # estimado
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
        "potencia_w": 110,      # estimado
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
        "potencia_w": 140,      # estimado
        "valor_maquina": 4000,  # estimado
        "vida_util_h": 3000,
    },
    "neptune4": {
        "label": "Elegoo Neptune 4",
        "potencia_w": 160,
        "valor_maquina": 2000,  # estimado (esgotado em lojas)
        "vida_util_h": 2000,
    },
    "neptune4_pro": {
        "label": "Elegoo Neptune 4 Pro",
        "potencia_w": 150,      # estimado
        "valor_maquina": 2800,
        "vida_util_h": 2000,
    },
    "prusa_mk4s": {
        "label": "Prusa MK4S",
        "potencia_w": 120,
        "valor_maquina": 5500,  # estimado (importado ~USD 925)
        "vida_util_h": 5000,
    },
    "prusa_mini_plus": {
        "label": "Prusa MINI+",
        "potencia_w": 80,
        "valor_maquina": 3200,  # estimado (importado)
        "vida_util_h": 4000,
    },
}
```

**Pegadinha crítica — potência vs. fonte:** A fonte de uma Ender 3 é 350W mas a média real de impressão é ~120W. Jamais usar a potência da fonte como preset. O campo `potencia_w` no form deve exibir um tooltip: *"Potência ativa média durante impressão (não a potência da fonte). Usar wattímetro para valor exato."*

---

## 2. Bandeiras Tarifárias ANEEL — Valores Vigentes 2025

> O adicional se SOMA à tarifa base da distribuidora. A fórmula correta é:
> `tarifa_efetiva = tarifa_base + adicional_bandeira`
> depois: `custo_energia = (potencia_w / 1000) * tempo_h * tarifa_efetiva`

| Bandeira | Adicional (R$/100 kWh) | Adicional (R$/kWh) | Status jun/2025 |
|----------|------------------------|---------------------|-----------------|
| Verde | R$ 0,00 | R$ 0,0000 | — |
| Amarela | R$ 1,885 | R$ 0,01885 | **ATIVA** (mai–jun 2025) [CITED: Jornal de Brasília / ANEEL] |
| Vermelha P1 | R$ 4,463 | R$ 0,04463 | — |
| Vermelha P2 | R$ 7,877 | R$ 0,07877 | — |
| Escassez Hídrica | R$ 14,200 | R$ 0,14200 | HISTÓRICA — não vigente desde jan/2022 |

**Fonte:** [CITED: Jornal de Brasília jun/2025 — ANEEL anuncia bandeira amarela para junho 2025]; valores do adicional [CITED: Agência Brasil / enel.com.br — Bandeiras Tarifárias 2025].

### Python dict pronto

```python
# apps/calculator/presets.py
BANDEIRAS_ANEEL = {
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
BANDEIRA_VIGENTE_DEFAULT = "amarela"  # atualizar mensalmente
```

**Como aplicar no form/serviço:**

1. O usuário informa a tarifa base da distribuidora (ex.: R$ 0,95/kWh — tarifa residencial típica BR 2025).
2. O usuário seleciona a bandeira atual.
3. O serviço calcula: `tarifa_efetiva = tarifa_base + bandeira["adicional_kwh"]`.
4. Usar `tarifa_efetiva` no cálculo de energia — NÃO substituir a tarifa base pela bandeira.

**Atenção:** A tarifa base varia por distribuidora e classe de consumo. O valor 0,95/kWh do `CustoDefaults` atual é uma média residencial razoável para SP/RJ/MG 2025 [ASSUMED — não verificado contra ANEEL por distribuidora].

---

## 3. Filamentos FDM — Tabela de Presets

| Material | Densidade (g/cm³) | Faixa preço BR (R$/kg) | Bico (°C) | Mesa (°C) | Dificuldade |
|----------|-------------------|------------------------|-----------|-----------|-------------|
| PLA | 1,24 | R$ 100–130 | 190–220 | 50–60 | Fácil |
| PLA+ | 1,24 | R$ 100–140 | 200–230 | 50–65 | Fácil |
| PETG | 1,27 | R$ 100–160 | 230–250 | 70–90 | Fácil–Médio |
| ABS | 1,05 | R$ 90–130 | 230–250 | 90–110 | Médio |
| ASA | 1,07 | R$ 160–220 | 240–260 | 90–110 | Médio |
| TPU 95A | 1,21 | R$ 120–180 | 220–240 | 40–60 | Médio |
| Nylon PA6/PA12 | 1,13 | R$ 230–350 | 240–270 | 70–90 | Difícil |
| PC (Policarbonato) | 1,20 | R$ 180–280 | 260–300 | 100–120 | Difícil |
| PLA-CF | 1,29 | R$ 170–220 | 200–230 | 50–65 | Médio |
| PETG-CF | 1,30 | R$ 180–250 | 240–260 | 70–90 | Médio |

**Fontes:** [CITED: slim3d.com.br — PLA R$119,90; PETG R$150; ABS R$99,90; ASA R$180; TPU R$120; PC R$180]; [CITED: filamentos3dbrasil.com.br — PLA-CF R$177,67]; [CITED: slim3d.com.br — PETG-CF R$199; Nylon PA6 R$229,90 via 3DX Filamentos]; densidades [ASSUMED — valores padrão da literatura de engenharia de polímeros, amplamente confirmados por fichas técnicas de fabricantes].

### Python dict pronto

```python
# apps/calculator/presets.py
FILAMENTOS = {
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
}
```

---

## 4. UX de Boas Calculadoras de Custo 3D

Com base na análise de Prusa Blog, printpal.io, 3dwithus.com e omnicalculator.com:

1. **Preset de impressora auto-preenche campos** — selecionar "Bambu Lab A1" preenche automaticamente potência (W), valor da máquina (R$) e vida útil (h). O usuário pode sobrescrever qualquer campo. Isso é o maior ganho de UX da v2.

2. **Preset de filamento auto-preenche preço/kg** — selecionar "PETG" preenche o preço/kg sugerido. O campo fica editável (usuário tem preço real da bobina).

3. **Separador visual bandeira tarifária** — campo de tarifa base separado de selector de bandeira (adicional). Exibir o valor efetivo calculado ao lado: *"Tarifa efetiva: R$ 0,97/kWh (base R$ 0,95 + Amarela R$ 0,019)"*.

4. **Breakdown com percentuais** — cada linha de custo exibe valor absoluto E porcentagem do custo total. Permite ao usuário ver imediatamente qual fator domina (geralmente material ou mão de obra).

5. **Cálculo 100% client-side em JS** — sem round-trip ao servidor; atualização em tempo real enquanto o usuário digita. O servidor valida via `PricingService.calcular()` apenas no submit do orçamento.

6. **Link compartilhável / copiar resultado** — gerar URL com params ou botão "Copiar resumo" (texto formatado). Prusa implementa via query string. [CITED: blog.prusa3d.com/how-to-calculate-printing-costs]

---

## 5. Pegadinhas Técnicas

### 5.1 Aplicar bandeira tarifária corretamente

```
ERRADO: tarifa_kwh = adicional_bandeira  # substitui a tarifa
CORRETO: tarifa_efetiva = tarifa_base + adicional_bandeira
         custo_energia = (W/1000) * h * tarifa_efetiva
```

O `PricingService.calcular()` atual recebe `tarifa_kwh` como valor único — a forma mais limpa é:
- Manter a assinatura como está (um único `tarifa_kwh`).
- Calcular `tarifa_kwh = tarifa_base + adicional_bandeira` no form/view ANTES de chamar o serviço.
- O form pode expor dois campos (tarifa_base + bandeira) e o método `to_calc_data()` faz a soma.

### 5.2 Arredondamento monetário

O serviço já usa `Decimal` + `ROUND_HALF_UP` — correto. Não mudar. O JS client-side deve replicar com `Math.round(x * 100) / 100` para exibição; aceitar diferença de ±R$ 0,01 entre JS e Python (floating point) — nunca usar o resultado JS como dado final de orçamento, apenas para preview.

### 5.3 Espelhamento JS ↔ servidor

- Fórmulas: idênticas e comentadas nos dois lados.
- O servidor é a fonte da verdade para valores em PDF/orçamento formal.
- O JS é apenas UX de preview em tempo real.
- Validação de formulário: sempre via Django form no submit (nunca só JS).

### 5.4 Atualização de presets

- Preços de filamento mudam com frequência — definir `FILAMENTOS[...]["preco_kg_default"]` como sugestão inicial, nunca como valor bloqueado.
- Bandeiras ANEEL mudam mensalmente — o `BANDEIRA_VIGENTE_DEFAULT` deve ser documentado com data de última atualização no código.
- Potência de impressoras: valores mais estáveis, raramente mudam entre revisões.

---

## Assumptions Log

| # | Claim | Seção | Risco se errado |
|---|-------|-------|-----------------|
| A1 | Ender 3 V3 SE potência média 100W | §1 | Subestimar custo de energia; diferença ~R$ 0,01–0,03/hora de impressão |
| A2 | Ender 3 V3 KE/V3 potência 120–130W | §1 | Idem |
| A3 | K1 Max potência 150W | §1 | Sem medição publicada; pode ser 130–200W |
| A4 | Bambu A1 potência 110W | §1 | Bambu documenta 50–200W de range; média real depende do material |
| A5 | Kobra 3 Combo potência 140W / valor R$ 4.000 | §1 | Preço não encontrado em lojas BR; estimado por analogia |
| A6 | Neptune 4 (não Pro) preço BR ~R$ 2.000 | §1 | Produto esgotado nas fontes consultadas |
| A7 | Prusa MK4S BR R$ 5.000–6.000 | §1 | Importado sem loja oficial BR; câmbio e impostos variam |
| A8 | Tarifa base residencial BR 0,95/kWh | §2 | Varia por distribuidora/classe; ANEEL não publica média única |
| A9 | Densidades dos filamentos | §3 | Fichas técnicas de fabricantes variam ±5%; impacto baixo no cálculo de custo |

---

## Fontes

- [Bambu Lab Forum — Power Consumption Data X1 Series](https://forum.bambulab.com/t/power-consumption-data/4180) — medição wattímetro X1C 103–135W
- [Bambu Lab Forum — P1S Power Consumption](https://forum.bambulab.com/t/p1s-power-consumption/173002) — range 105–145W
- [call-3d.com — Bambu Lab Power Consumption Guide](https://www.call-3d.com/blogs/upgrades/bambu-lab-power-consumption-review) — A1 Mini ~90W, A1 50–200W
- [xargas.eu — Prusa MK4S + MMU3 Power Consumption (2025)](https://xargas.eu/3dprint/2025-12-30-PrusaMK4SMMU3PowerConsumption.html) — PETG: 160W, idle: 15W
- [prusa3d.com — MK4S product page](https://www.prusa3d.com/product/original-prusa-mk4-2/) — 80W PLA / 120W ABS oficial; USD 925
- [3dsolved.com — Ender 3 Power Consumption](https://3dsolved.com/ender-3-power-consumption/) — Ender 3 original ~120–130W
- [Creality K1 review — pea3d.com / 3dprintbeginner.com](https://pea3d.com/en/creality-3d-electricity-cost-calculator-ender-k1-analysis/) — K1 ~100W pós-aquecimento
- [Elegoo Neptune 4 review — igorslab.de](https://www.igorslab.de/en/elegoo-neptune-4-3d-drucker-im-test/6/) — 160–190W imprimindo PLA
- [bestlayer3d.com.br — Neptune 4 Pro](https://bestlayer3d.com.br/produtos/impressora-3d-elegoo-neptune-4-pro/) — R$ 2.800
- [gtmax3d.com.br — Bambu Lab A1 Mini](https://www.gtmax3d.com.br/impressora-3d-bambu-lab-a1-mini) — R$ 2.319
- [gtmax3d.com.br — Bambu Lab A1](https://www.gtmax3d.com.br/impressora-3d-bambu-lab-a1) — R$ 3.529
- [MercadoLivre BR — Bambu Lab P1S Combo](https://www.mercadolivre.com.br/impressora-3d-bambu-lab-p1s-combo-ams/p/MLB33997681) — R$ 7.789
- [MercadoLivre BR — Bambu Lab X1 Carbon Combo](https://www.mercadolivre.com.br/impressora-3d-x1-carbon-fechada-c-ams-lite-combo-bambu-lab-cor-branco/p/MLB45005727) — R$ 15.463
- [MercadoLivre BR — Ender 3 V3 SE](https://www.mercadolivre.com.br/impressora-3d-creality-3d-ender-3-v3-se/p/MLB33998539) — R$ 1.499
- [MercadoLivre BR — Ender 3 V3](https://www.mercadolivre.com.br/impressora-3d-creality-ender-3-v3-cor-cinza-com-tecnologia-de-impresso-fdm/p/MLB44126946) — R$ 2.339
- [slim3d.com.br — Ender 3 V3 KE](https://www.slim3d.com.br/equipamentos/impressoras-3d-filamento-fdm/creality/creality-ender-3-v3-ke) — R$ 2.199
- [slim3d.com.br — K1 Max](https://www.slim3d.com.br/equipamentos/impressoras-3d-filamento-fdm/creality/creality-k1-max) — R$ 9.499
- [slim3d.com.br — K1](https://www.slim3d.com.br/equipamentos/impressoras-3d-filamento-fdm/creality/creality-k1) — R$ 4.130
- [slim3d.com.br — ASA R$ 180/kg](https://www.slim3d.com.br/produtos/filamento-asa-premium-1kg-slim-3d)
- [slim3d.com.br — filamentos (PLA, PETG, ABS, TPU, PC)](https://www.slim3d.com.br/filamentos-3d)
- [Jornal de Brasília — Bandeira Amarela junho 2025](https://jornaldebrasilia.com.br/noticias/economia/mes-de-junho-tera-bandeira-tarifaria-amarela-mesmo-nivel-de-maio-define-aneel/)
- [enel.com.br / ANEEL — valores das bandeiras tarifárias 2025](https://www.enel.com.br/pt-saopaulo/midia/news/d2025-9/outubro-tera-bandeira-tarifaria-reduzida-na-conta-de-luz-para-vermelha-patamar-1.html)
- [blog.prusa3d.com — How to Calculate Printing Costs (UX)](https://blog.prusa3d.com/how-to-calculate-printing-costs_38650/)
