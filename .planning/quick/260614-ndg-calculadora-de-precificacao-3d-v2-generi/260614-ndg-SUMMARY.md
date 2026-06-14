---
phase: quick-260614-ndg
plan: "01"
subsystem: calculator
tags: [calculator, pricing, presets, aneel, ui, js, css, readme]
dependency_graph:
  requires: []
  provides: [calculadora-v2-presets, calculadora-v2-bandeira-aneel, calculadora-v2-ui, calculadora-v2-orcamento, readme-l3d-labz]
  affects: [apps/calculator, static/js/calculator.js, static/css/theme.css, README.md]
tech_stack:
  added: []
  patterns:
    - presets em módulo próprio (apps/calculator/presets.py)
    - tarifa efetiva calculada no form.to_calc_data() antes do serviço
    - json_script para passar dados Python ao JS sem hardcode
    - breakdown com barras CSS (calc-bar/calc-bar-fill) via tokens
    - permalink via history.replaceState; reidratação no init
key_files:
  created:
    - apps/calculator/presets.py
  modified:
    - apps/calculator/forms.py
    - apps/calculator/views.py
    - apps/calculator/templates/calculator/publica.html
    - apps/calculator/templates/calculator/orcamento.html
    - static/js/calculator.js
    - static/css/theme.css
    - README.md
decisions:
  - "tarifa_efetiva = tarifa_base + adicional_bandeira calculada em CalcForm.to_calc_data() — mantém assinatura do PricingService inalterada"
  - "presets injetados via json_script (sem hardcode de números no JS ou HTML)"
  - "calculator.js reutilizado em orcamento.html apenas para UX (auto-preenchimento e tarifa efetiva); submit continua server-side"
  - "pdf.py inalterado — recebe só dados públicos (T-calc-01)"
metrics:
  duration: "~60 min"
  completed: "2026-06-14"
  tasks_completed: 4
  files_changed: 7
---

# Quick 260614-ndg: Calculadora de Precificação 3D v2 — Genérica, Presets, Bandeiras ANEEL, UI Profissional e README

Reformulação completa da calculadora de precificação 3D do L3D Labz em ferramenta genérica e profissional: módulo de presets (14 impressoras FDM, 10 filamentos, bandeiras ANEEL vigentes), tarifa efetiva por bandeira (base + adicional), UI em duas colunas com breakdown visual de barras proporcionais, permalink e botão Copiar, orçamento privado reaproveitando a mesma UI, e README reescrito sem Nexora.

## Tarefas Concluídas

| Tarefa | Nome | Commit | Arquivos-chave |
|--------|------|--------|----------------|
| 1 | presets.py + bandeira ANEEL + tarifa efetiva | f1f70f6 | presets.py, forms.py, views.py |
| 2 | UI pública profissional v2 + JS + CSS | 27b0133 | publica.html, calculator.js, theme.css |
| 3 | Orçamento privado v2 com presets e bandeira | 0cea257 | orcamento.html, theme.css |
| 4 | README reescrito alinhado ao L3D Labz | c351d63 | README.md |

## Detalhamento por Tarefa

### Task 1 — presets.py + tarifa efetiva

`apps/calculator/presets.py` criado com:
- `IMPRESSORAS` (14 modelos: Creality Ender 3 V3 SE/KE/V3, K1/K1 Max, Bambu A1 Mini/A1/P1S/X1C, Kobra 3, Neptune 4/Pro, Prusa MK4S/Mini+) + entrada `"manual"`
- `FILAMENTOS` (PLA, PLA+, PETG, ABS, ASA, TPU, Nylon, PC, PLA-CF, PETG-CF) + entrada `"manual"`
- `BANDEIRAS_ANEEL` (verde/amarela/vermelha1/vermelha2) com `adicional_kwh`; `BANDEIRA_VIGENTE_DEFAULT = "amarela"`
- Helpers: `impressora_choices()`, `filamento_choices()`, `bandeira_choices()`, `presets_json()`

`forms.py` atualizado:
- Adiciona `impressora` e `filamento` (ChoiceField de preset, apenas UX)
- Substitui `tarifa_kwh` único por `tarifa_base` + `bandeira`
- `to_calc_data()` calcula `adicional = BANDEIRAS_ANEEL[bandeira]["adicional_kwh"]` e soma à `tarifa_base`
- Verificado: `0.95 + 0.01885 = 0.96885` ✓

`views.py` atualizado: injeta `presets_json()` no contexto de ambas as views.

### Task 2 — UI pública + JS + CSS

`publica.html` reescrito:
- Cards por seção: Impressora, Filamento, Tempo, Energia (tarifa_base + bandeira + tarifa efetiva), Trabalho, Margem/Risco, Quantidade
- `{{ presets_json|json_script:"calc-presets" }}` no extra_head
- Breakdown com `.calc-row-item` / `.calc-bar` / `.calc-bar-fill` por componente
- `aria-live` no painel de resultado, `label for` em todos os inputs
- Custo/hora, total por quantidade (ocultado quando qtd=1), botão Copiar resultado

`calculator.js` reescrito (IIFE, "use strict"):
- Lê presets de `#calc-presets` via `JSON.parse(textContent)`
- Auto-preenchimento: impressora → potencia_w/valor_maquina/vida_util_h; filamento → preco_kg
- `tarifa_efetiva = tarifa_base + adicional_bandeira` (adicional dos presets)
- Fórmulas comentadas e idênticas ao Python (`PricingService.calcular`)
- Breakdown: `%` de cada componente sobre `custo_total`, largura das barras via `style.width`
- Permalink: `history.replaceState` a cada input; reidratação no `init()`
- Copiar: `navigator.clipboard.writeText` + fallback `execCommand`

`theme.css` ampliado (a partir de ~linha 2250):
- `.calc-col-title`, `.calc-row-item`, `.calc-row-header`
- `.calc-bar` (trilho, `--border-soft`) e `.calc-bar-fill` (`--accent`, `transition width`)
- `.calc-bar-fill--warn` (`--accent-2` para ajuste de falha)
- `.calc-pct`, `.calc-tarifa-efetiva`, `.calc-custo-hora`, `.calc-total-qtd`, `.calc-valor-total`
- `.calc-select-preset`, `.calc-btn-copiar`
- Regras `@media print` preservadas + `.calc-btn-copiar` ocultado na impressão

### Task 3 — Orçamento privado v2

`orcamento.html` atualizado:
- Inclui `{{ presets_json|json_script:"calc-presets" }}` e `calculator.js` para auto-preenchimento UX
- Cards espelhando a publica: Impressora (select + potencia/valor/vida_util), Filamento (select + peso/preco), Tempo, Energia (tarifa_base + bandeira + tarifa efetiva via JS), Trabalho, Margem/Risco
- Submit continua 100% server-side; `OrcamentoForm.to_calc_data()` soma a bandeira antes do serviço
- PDF gerado apenas com `{cliente_nome, peca_descricao, quantidade, prazo_entrega, observacoes, preco_venda, total}` — pdf.py inalterado (T-calc-01)

### Task 4 — README

`README.md` completamente reescrito em pt-br:
- Título "L3D Labz — Impressão 3D sob demanda" (sem Nexora)
- Tabela de features reais com rotas
- Stack completa (Django, DRF, model-viewer, JS vanilla, reportlab, whitenoise, Postgres/Redis)
- Tabela de camadas arquiteturais
- Seção dedicada à Calculadora v2 (presets, bandeiras ANEEL, breakdown, permalink)
- Como rodar com venv/pip/migrate/seed_demo/createsuperuser/runserver
- Tabela de variáveis de ambiente
- Checkout/pedidos e próximos passos
- Nenhuma menção a "nexora" (verificado via assert)

## Deviations from Plan

None — plano executado exatamente como escrito.

## Known Stubs

- Link WhatsApp no CTA da calculadora pública (`href="https://wa.me/5511999999999..."`) — número placeholder. Substituir pelo número real da L3D Labz quando disponível (comentado no template).

## Threat Surface Scan

Nenhuma superfície nova não prevista no plano. As mitigações T-calc-01, T-calc-02, T-calc-03, T-calc-04 foram verificadas:
- T-calc-01: pdf.py inalterado, recebe só dados públicos — OK
- T-calc-02: cálculo JS é preview; orçamento formal recalcula server-side — OK
- T-calc-03: `@user_passes_test(lambda u: u.is_staff)` mantido — OK
- T-calc-04: nenhum novo pacote instalado — OK

## Self-Check: PASSED

Arquivos criados/modificados:
- `apps/calculator/presets.py` — FOUND
- `apps/calculator/forms.py` — FOUND (atualizado)
- `apps/calculator/views.py` — FOUND (atualizado)
- `apps/calculator/templates/calculator/publica.html` — FOUND
- `apps/calculator/templates/calculator/orcamento.html` — FOUND
- `static/js/calculator.js` — FOUND
- `static/css/theme.css` — FOUND
- `README.md` — FOUND

Commits:
- f1f70f6 — FOUND
- 27b0133 — FOUND
- 0cea257 — FOUND
- c351d63 — FOUND
