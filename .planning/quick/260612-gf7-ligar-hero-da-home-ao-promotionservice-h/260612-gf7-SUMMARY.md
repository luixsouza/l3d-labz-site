---
phase: quick-260612-gf7
plan: "01"
subsystem: core/promotions
tags: [hero, home, promotions, view, template]
dependency_graph:
  requires: [apps.promotions.services.PromotionService]
  provides: [hero_promo no contexto da HomeView, renderização condicional do hero na home]
  affects: [apps/core/views.py, apps/core/templates/core/home.html]
tech_stack:
  added: []
  patterns: [deferred import para evitar ciclo promotions→core, if/else template para hero condicional]
key_files:
  modified:
    - apps/core/views.py
    - apps/core/templates/core/home.html
decisions:
  - Deferred import de PromotionService dentro de get_context_data (mesmo padrão do CatalogService)
  - CTA secundário 'Faça meu Lithophane' duplicado em ambos os ramos do if/else
metrics:
  duration_min: 8
  completed_date: "2026-06-12"
  tasks_completed: 2
  files_modified: 2
---

# Phase quick-260612-gf7 Plan 01: Hero Promocional na Home Summary

**One-liner:** Ligação da HomeView ao PromotionService para exibir hero promocional dinâmico (badge/título/subtítulo/CTA) com fallback hardcoded quando não há promoção ativa.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Passar hero_promo no contexto da HomeView | a31106d | apps/core/views.py |
| 2 | Renderizar hero promocional condicional no template | 3dd7fb6 | apps/core/templates/core/home.html |

## What Was Built

### Task 1 — apps/core/views.py
`HomeView.get_context_data` agora importa `PromotionService` via deferred import (dentro da função, mesmo padrão de `CatalogService`) e injeta `context["hero_promo"] = PromotionService.get_hero_promotion()`. O retorno é `dict | None` dependendo da existência de promoção hero ativa.

### Task 2 — apps/core/templates/core/home.html
O bloco hero (section + geek-hero) foi envolvido em `{% if hero_promo %}...{% else %}...{% endif %}`:
- **Ramo if:** Usa `{{ hero_promo.badge }}`, `{{ hero_promo.title }}`, `{{ hero_promo.subtitle }}`, `{{ hero_promo.cta_url }}`, `{{ hero_promo.cta_label }}` — mesma estrutura HTML e classes existentes.
- **Ramo else:** Hero hardcoded original preservado byte a byte.
- **CTA secundário** 'Faça meu Lithophane' presente nos dois ramos.
- Zero CSS novo.

## Verification

- `python manage.py check` — 0 issues.
- views.py: `hero_promo` presente, `PromotionService.get_hero_promotion()` chamado.
- home.html: `{% if hero_promo %}`, `hero_promo.badge`, `hero_promo.title`, `hero_promo.subtitle`, `hero_promo.cta_url`, `hero_promo.cta_label` presentes; CTA Lithophane em ambos os ramos; fallback hardcoded intacto.

## Deviations from Plan

None — plano executado exatamente como escrito.

## Known Stubs

None.

## Threat Flags

None — sem novo endpoint de rede, sem novo caminho de auth, sem acesso a arquivo novo.

## Self-Check: PASSED

- [x] apps/core/views.py modificado com hero_promo
- [x] apps/core/templates/core/home.html modificado com bloco condicional
- [x] Commit a31106d existe (Task 1)
- [x] Commit 3dd7fb6 existe (Task 2)
