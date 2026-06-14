---
phase: quick-260614-lzm
plan: "01"
subsystem: calculator
tags: [calculadora, precificacao, impressao-3d, pdf, reportlab, staff, vanillajs]
dependency_graph:
  requires: [apps.core, apps.accounts]
  provides: [apps.calculator, /calculadora/, /calculadora/orcamento/]
  affects: [navbar, config.urls, requirements.txt, static/css/theme.css]
tech_stack:
  added: [reportlab==4.5.1]
  patterns: [PricingService stateless, gerar_orcamento_pdf isolado, IIFE vanilla JS, to_calc_data()]
key_files:
  created:
    - apps/calculator/__init__.py
    - apps/calculator/apps.py
    - apps/calculator/services.py
    - apps/calculator/forms.py
    - apps/calculator/mappers.py
    - apps/calculator/admin.py
    - apps/calculator/views.py
    - apps/calculator/urls.py
    - apps/calculator/pdf.py
    - apps/calculator/templates/calculator/publica.html
    - apps/calculator/templates/calculator/orcamento.html
    - static/js/calculator.js
  modified:
    - config/settings/base.py
    - config/urls.py
    - apps/core/templates/core/partials/navbar.html
    - static/css/theme.css
    - requirements.txt
decisions:
  - "D-01: PricingService.calcular é a fonte única da verdade das fórmulas — reutilizado pela view de orçamento (server-side) e espelhado em JS (client-side)"
  - "D-03: PDF de orçamento recebe SOMENTE {cliente, peça, qtd, prazo, obs, preco_venda, total} — custos internos nunca entram no gerar_orcamento_pdf"
  - "D-04: reportlab==4.5.1 (pura-python, sem deps nativas, funciona Windows dev + Docker Linux prod)"
  - "D-05: CustoDefaults dataclass frozen centraliza os defaults editáveis num único lugar"
  - "Importação de pdf.py diferida (dentro da view orcamento) para permitir staging incremental da Task 2 sem Task 3 criada"
metrics:
  duration: "~45 min"
  completed_date: "2026-06-14"
---

# Quick Task 260614-lzm: Calculadora de Precificação de Impressão 3D — Summary

**One-liner:** Calculadora de precificação 3D com cálculo client-side em tempo real (vanilla JS + PricingService Python) e emissão de PDF de orçamento protegido por is_staff (reportlab, sem expor custos internos).

## Tarefas Executadas

| Tarefa | Nome | Commit | Arquivos-chave |
|--------|------|--------|----------------|
| 1 | Scaffold do app + fórmulas + forms | `253eb86` | services.py, forms.py, mappers.py, apps.py |
| 2 | Calculadora pública + JS + CSS + navbar | `436f4b6` | views.py, publica.html, calculator.js, theme.css |
| 3 | Calculadora privada + PDF + requirements | `3b94df7` | pdf.py, orcamento.html, requirements.txt |

## O que foi construído

### apps/calculator (novo app stateless)

- **PricingService.calcular()** — 8 chaves de saída com Decimal (custo_material, custo_energia, custo_depreciacao, custo_maoobra, subtotal, ajuste_falha, custo_total, preco_venda). Verificado: 50g PLA a R$120/kg, 110W, 4h → custo_material=R$6,00, custo_depreciacao=R$4,00, preco_venda=R$56,15 com margem 150%.
- **CustoDefaults** — dataclass frozen com defaults centralizados (tarifa=0.95, margem=150%, falha=10%, 110W/Ender3).
- **CalcForm / OrcamentoForm** — 10 inputs de custo + 5 campos de cliente; `to_calc_data()` converte cleaned_data para PricingService.
- **PricingMapper.to_display()** — aplica format_brl em todas as chaves monetárias.
- **gerar_orcamento_pdf()** — PDF profissional L3D Labz com reportlab/platypus: cabeçalho verde, tabela de precificação, total em destaque. Custos internos NUNCA entram neste módulo (T-calc-02 mitigado).

### Rotas e integração

- `GET /calculadora/` → calculadora pública aberta (200), detalhamento completo de 8 custos, CTA WhatsApp.
- `GET/POST /calculadora/orcamento/` → protegida por `@user_passes_test(lambda u: u.is_staff)`; anônimo → 302.
- POST de staff: valida OrcamentoForm, recalcula via PricingService server-side, retorna PDF como `Content-Disposition: attachment`.

### Frontend

- `static/js/calculator.js` (IIFE, defer, sem framework): espelha EXATAMENTE as fórmulas do PricingService; cálculo 100% client-side em tempo real via `input`/`change`; formatação BRL via `toLocaleString('pt-BR', ...)`.
- CSS: bloco `.calc-*` adicionado ao theme.css usando exclusivamente os tokens existentes (--bg-card, --border, --accent, --font-mono, etc.); layout 2 colunas com sticky no desktop; regra `@media print`.
- Navbar: link "Calculadora" com active state `vn == 'calculator:publica'`.

## Verificações Executadas

| Verificação | Resultado |
|-------------|-----------|
| PricingService.calcular(50g, R$120/kg, 110W, 4h, ...) → custo_material=6.00 | PASS |
| PricingService.calcular(50g, ...) → custo_depreciacao=4.00 | PASS |
| PricingService devolve as 8 chaves exigidas | PASS |
| gerar_orcamento_pdf() → bytes começando com `%PDF-`, len>800 | PASS (2572 bytes) |
| PDF não contém 'custo_material', 'subtotal', 'margem' etc. | PASS |
| GET /calculadora/ → 200 + calculator.js + 'Precificação' | PASS |
| GET /calculadora/orcamento/ (anônimo) → 302 | PASS |
| GET /calculadora/orcamento/ (staff) → 200 + formulário | PASS |
| manage.py check | 0 issues |
| manage.py makemigrations --check --dry-run | No changes detected |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Importação de pdf.py diferida na view**
- **Found during:** Task 2 — ao verificar GET /calculadora/, a importação `from .pdf import gerar_orcamento_pdf` no topo de views.py quebrava o módulo porque pdf.py ainda não existia (Task 3).
- **Fix:** Moved the import inside the `orcamento` POST branch as a deferred import (standard Python pattern, já usado no codebase em `apps/catalog/services.py:58`).
- **Files modified:** apps/calculator/views.py
- **Commit:** `436f4b6`

## Known Stubs

- CTA WhatsApp em `publica.html`: número de telefone `5511999999999` é placeholder. Comentado no template como "Substituir pelo número real ou URL de contato quando disponível."

## Threat Flags

Nenhuma superfície nova fora do threat_model do plano.

## Self-Check: PASSED

- apps/calculator/services.py: FOUND
- apps/calculator/pdf.py: FOUND
- apps/calculator/views.py: FOUND
- static/js/calculator.js: FOUND
- apps/calculator/templates/calculator/publica.html: FOUND
- apps/calculator/templates/calculator/orcamento.html: FOUND
- Commits 253eb86, 436f4b6, 3b94df7: FOUND (git log --oneline -5)
