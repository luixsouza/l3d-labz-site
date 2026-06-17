---
phase: quick-260617-mrl
plan: 01
subsystem: calculator, core/partials
tags: [calculator, pricing, navbar, footer, skin-maker, mockup]
dependency_graph:
  requires: []
  provides: [lean-pricing-formula, calc-mockup-layout, navbar-skin-maker, footer-skin-maker]
  affects: [apps/calculator, apps/core/templates/core/partials, static/js/calculator.js, static/css/theme.css]
tech_stack:
  added: []
  patterns: [lean-pricing-formula, chips-ux, permalink-querystring]
key_files:
  created: []
  modified:
    - apps/calculator/presets.py
    - apps/calculator/forms.py
    - apps/calculator/services.py
    - apps/calculator/templates/calculator/publica.html
    - apps/calculator/templates/calculator/orcamento.html
    - static/js/calculator.js
    - static/css/theme.css
    - apps/core/templates/core/partials/navbar.html
    - apps/core/templates/core/partials/footer.html
decisions:
  - "Fórmula enxuta: remove depreciação (valor_maquina/vida_util_h) e taxa_falha_pct; adiciona custos_fixos"
  - "valor_kwh é campo único direto (sem soma tarifa_base+bandeira no form)"
  - "Chips de bandeira preenchem valor_kwh via data-kwh com |unlocalize (gotcha pt-br)"
  - "OrcamentoService inalterado: recebe só 7 campos públicos (T-mrl-01 preservado)"
metrics:
  duration: "~45min"
  completed: "2026-06-17"
  tasks_completed: 3
  tasks_total: 4
  files_changed: 9
---

# Phase quick-260617-mrl Plan 01: Calculadora mockup + navbar/footer skin maker

**One-liner:** Modelo enxuto de precificação (5 custos, sem depreciação/falha) com layout 3 cards do mockup e navbar/footer no skin maker.

## Tasks Executadas

### Task 1 — Modelo de cálculo enxuto (presets + forms + service + orcamento staff)

**Commit:** `e6a9e90`
**Arquivos:** `apps/calculator/presets.py`, `apps/calculator/forms.py`, `apps/calculator/services.py`, `apps/calculator/templates/calculator/orcamento.html`

**O que mudou:**
- `PricingService.calcular`: fórmula enxuta com 6 chaves de saída (`custo_material`, `custo_energia`, `custo_maoobra`, `custos_fixos`, `subtotal`, `preco_venda`). Remove `custo_depreciacao`, `ajuste_falha`, `custo_total`.
- Parâmetros removidos: `valor_maquina`, `vida_util_h`, `taxa_falha_pct`, `tarifa_kwh` → substituído por `valor_kwh` direto.
- `CustoDefaults`: remove `taxa_falha_pct`, `valor_maquina`, `vida_util_h`; `tarifa_kwh` → `valor_kwh`.
- `presets.py`: remove `IMPRESSORAS`/`BANDEIRAS_ANEEL` do JSON público; adiciona `CONSUMO_CHIPS` (3 chips) e `BANDEIRA_KWH` (3 bandeiras simplificadas). `presets_json()` retorna `filamentos`, `consumo_chips`, `bandeira_kwh`.
- `CalcForm`: remove campos `impressora`, `valor_maquina`, `vida_util_h`, `tarifa_base`, `bandeira`, `taxa_falha_pct`; adiciona `custos_fixos` e `valor_kwh`. `to_calc_data()` retorna 8 chaves enxutas.
- `orcamento.html` (staff): 3 cards (Filamento / Energia e Tempo / Opcionais); remove card "Impressora".

**Verify resultado:**
```
PricingService.calcular(peso_g=130, preco_kg=120, potencia_w=200, tempo_h=6,
  valor_kwh=1.00, custo_maoobra=20, custos_fixos=0, margem_pct=100)
=> {'custo_material': 15.6, 'custo_energia': 1.2, 'custo_maoobra': 20.0,
    'custos_fixos': 0.0, 'subtotal': 36.8, 'preco_venda': 73.6}  ✓
manage.py check: 0 issues  ✓
```

---

### Task 2 — Calculadora pública no layout do mockup (template + JS + CSS)

**Commit:** `f9555b0` + fix `808e50a`
**Arquivos:** `apps/calculator/templates/calculator/publica.html`, `static/js/calculator.js`, `static/css/theme.css`

**O que mudou:**
- `publica.html`: reescrito com 3 cards (Filamento / Energia e Tempo / Opcionais) conforme `image.png`. Grid `.calc-grid-3` de 3 colunas por card. Inputs com sufixo `.calc-suffix`. Chips `.pill[data-w]`/`[data-kwh]`/`[data-margem]`. Botões `#btnPuxarPreco`, `#btnRestaurarPreco`, `#btnCalcular`, `#btnLimpar`. Resultado enxuto sem depreciação/falha.
- **Fix (Rule 1):** `data-kwh="{{ kwh|unlocalize }}"` — sem `|unlocalize`, Django renderizava `0,95` (vírgula pt-br) que o JS parseava como NaN. Detectado na verificação headless.
- `calculator.js`: fórmula enxuta (sem `custo_depreciacao`, `ajuste_falha`, `taxa_falha`, `valor_maquina`, `vida_util_h`, `tarifa_base`, `bandeira`). Implementa chips com `marcarChipAtivo()`. `btnPuxarPreco` e `btnRestaurarPreco` usam a mesma referência (`FILAMENTOS[key].preco_kg_default`). `btnLimpar` reseta form e chips. `CAMPOS_PERMALINK` atualizado. `copiarResultado()` com linhas enxutas.
- `theme.css`: adicionado ao fim do arquivo (vence cascata) — `.calc-card-header`, `.calc-card-ic`, `.calc-grid-3`, `.calc-input-wrap`, `.calc-suffix`, `.calc-chips`, `.calc-price-btns`, `.calc-form-footer`, `.calc-label-opt`. Compatível com temas claro/escuro.

**Verify:**
```
manage.py check: 0 issues  ✓
JS sem campos mortos (custo_depreciacao/ajuste_falha/taxa_falha): OK  ✓
JS com campos novos (valor_kwh/custos_fixos): OK  ✓
publica.html tem id_valor_kwh/id_custos_fixos/btnPuxarPreco/btnCalcular: count=6  ✓
```

**Checagem funcional headless (Playwright):**
- Preenchido: peso=130g, preco=120R$/kg, 200W, 6h, kWh=1,00, m.obra=20, fixos=0, margem=100%
- Resultado: **R$ 73,60** ✓
- Chip 200W preenche `id_potencia_w`: ✓
- Chip bandeira verde preenche `id_valor_kwh` = 0.95: ✓
- `btnPuxarPreco` para PLA preenche `id_preco_kg` = 120.0: ✓

---

### Task 3 — Navbar/footer no skin maker

**Commit:** `42a55e4`
**Arquivos:** `apps/core/templates/core/partials/navbar.html`, `apps/core/templates/core/partials/footer.html`

**O que mudou:**
- `navbar.html`: substituído `<svg #i-l3d-mark>` + `<b>L3D</b> Labz` por markup skin maker:
  ```html
  <span class="brand-badge"><img src="{% static 'img/logo.png' %}" alt=""></span>
  <span class="brand-word">L3D <span class="brand-labz">Labz</span></span>
  ```
  Nav, header-actions, aria-label inalterados.
- `footer.html`: 1ª coluna do `.footer-grid` vira `.footer-brand-block`:
  ```html
  <a href="..." class="brand footer-brand"><span class="brand-badge"><img ...></span></a>
  <div class="footer-brand-block">
    <span class="mascot-name">L3D <b>Labz</b></span>
    <p class="mascot-sub">Peças impressas em 3D...</p>
  </div>
  ```
  A regra CSS linha ~1695 (`mascot-name` uniforme sem verde) é preservada.

**Verify:**
```
manage.py check: 0 issues  ✓
navbar brand-badge/brand-labz: 2 ocorrências  ✓
footer footer-brand-block/mascot-name: 4 ocorrências  ✓
```

---

## Deviações do Plano

### Auto-fixadas

**1. [Rule 1 - Bug] data-kwh com vírgula pt-br (chip de bandeira quebrado)**
- **Encontrado durante:** Task 2 — verificação funcional headless (Playwright)
- **Problema:** Template renderizava `data-kwh="0,95"` (vírgula locale pt-br), o JS parseava `parseFloat("0,95")` → NaN → chip não preenchía `id_valor_kwh`
- **Fix:** Adicionado `|unlocalize` no loop de chips de bandeira: `data-kwh="{{ kwh|unlocalize }}"`
- **Arquivos:** `apps/calculator/templates/calculator/publica.html`
- **Commit:** `808e50a`

---

## Screenshots Capturados

| Arquivo | Descrição |
|---------|-----------|
| `shots/calc-light.png` | Calculadora tema CLARO, coluna única, valores do mockup — R$ 73,60 (full-page, recapturado) |
| `shots/calc-dark.png` | Calculadora tema ESCURO, coluna única, fundo escuro confirmado — R$ 73,60 (full-page, recapturado) |
| `shots/calc-light-top.png` | Topo (viewport) tema claro — confirma navbar fixa |
| `shots/calc-dark-top.png` | Topo (viewport) tema escuro — confirma navbar fixa |
| `shots/calc-dark-7360.png` | (anterior, 2 colunas) Calculadora tema escuro — R$ 73,60 |
| `shots/calc-light-7360.png` | (anterior, 2 colunas) Calculadora tema claro — R$ 73,60 |
| `shots/home-dark.png` | Home tema escuro (navbar + footer skin maker) |
| `shots/home-light.png` | Home tema claro (navbar + footer skin maker) |

---

## Checagem Funcional — R$ 73,60

**PASSOU** ✓

Valores do mockup preenchidos via Playwright:
- peso_g = 130, preco_kg = 120, potencia_w = 200, tempo_h = 6
- valor_kwh = 1.00, custo_maoobra = 20, custos_fixos = 0, margem_pct = 100

Resultado obtido em `#res_preco_venda`: **R$ 73,60**
Subtotal: R$ 36,80 | Material: R$ 15,60 | Energia: R$ 1,20 ✓

---

## Follow-up — Ajustes pós-revisão do checkpoint (2026-06-17)

**Commit:** `63ca075` — `fix(quick-260617-mrl): calculadora em coluna unica (igual ao mockup) + dark theme`
**Arquivo:** `static/css/theme.css`

A revisão do checkpoint apontou 2 desvios; ambos resolvidos:

**Ajuste 1 — Coluna única (layout do mockup):**
- `.calc-layout` deixou de ser `grid` de 2 colunas (form | resultado sticky) e virou `flex` column única centralizada (`max-width: 920px; margin: 2rem auto 0`).
- O painel de detalhamento/resultado agora aparece **full-width ABAIXO** do form (removido `position: sticky` lateral). "Copiar resultado" e o CTA "Pedir orçamento com a L3D" seguem abaixo do resultado.
- Os 3 campos por card (`.calc-grid-3`) continuam lado a lado; chips e botões "Puxar/Restaurar preço" preservados.
- Responsivo preservado: `.calc-grid-3` empilha em 1 coluna em telas ≤680px.
- Removida a regra `@media print` que referenciava `grid-template-columns` morto.

**Ajuste 2 — Tema escuro da calculadora:**
- Causa dos screenshots claro/escuro idênticos: a captura anterior **não** setava `localStorage`. O default da página é `data-theme="light"` (inline script aplica o tema salvo), então sem setar localStorage tudo saía claro.
- Não havia bg claro forçado na página — só nos inputs/selects sob `[data-theme="light"]` (correto). A calculadora já respeitava o tema escuro.
- Nova captura: `localStorage.setItem('l3d-theme', <tema>)` → `reload` → screenshot. Confirmado via `getComputedStyle(document.body).backgroundColor`:
  - claro: `rgb(250, 251, 249)` (claro) ✓
  - escuro: `rgb(10, 13, 21)` (escuro, igual à home) ✓
- `manage.py check`: 0 issues ✓
- R$ 73,60 reconfirmado em ambos os temas ✓

---

## Checkpoint — Validação Visual (Task 4)

**Status: PENDENTE DE APROVAÇÃO HUMANA**

Os screenshots foram capturados e estão em `.planning/quick/260617-mrl-calc-mockup-navbar-footer/shots/`.

Para validar visualmente:
1. Compare `shots/calc-dark-7360.png` e `shots/calc-light-7360.png` contra `image.png` (mockup).
2. Verifique: 3 cards (Filamento / Energia e Tempo / Opcionais), chips de potência e bandeira visíveis, botões "Puxar preço do site" e "Restaurar preço automático", botão largo "Calcular Custo" + "Limpar", e painel de resultado sem depreciação/falha.
3. Verifique navbar: logo badge + "L3D Labz" (Labz em verde).
4. Verifique footer: mascot-name "L3D Labz" + mascot-sub + demais colunas.
5. Confirme que claro/escuro ambos estão legíveis.

Digite "aprovado" ou descreva os ajustes visuais necessários.

---

## Known Stubs

Nenhum stub identificado. Todos os dados fluem de presets reais e cálculos em tempo real.

## Threat Flags

Nenhum novo surface identificado. T-mrl-01 preservado: OrcamentoService só recebe 7 campos públicos.
