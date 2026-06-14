---
phase: quick-260614-q6g
plan: "01"
subsystem: frontend/catalog
tags: [css-tokens, light-theme, hero-3d, model-viewer, rebrand]
dependency_graph:
  requires: []
  provides: [light-theme-palette, hero-3d-wiring]
  affects: [home, catalog, product-detail, checkout]
tech_stack:
  added: []
  patterns: [token-cascade-reconciliation, service-staticmethod, mapper-to-dict, thin-view]
key_files:
  created: []
  modified:
    - static/css/theme.css
    - apps/catalog/mappers.py
    - apps/catalog/services.py
    - apps/core/views.py
    - apps/core/templates/core/home.html
decisions:
  - "Terceiro bloco [data-theme=light] alinhado a paleta travada (verde #2FA84F/#43C266/#1E8C3E) em vez de remover — preserva estrutura de cascata para futuras extensoes"
  - "hero_3d injetado em ambos os ramos do hero (com e sem hero_promo) para garantir viewer independente do estado da promocao"
  - "Script model-viewer gated por hero_3d no extra_js — nao carrega o CDN quando DB nao tem produto 3D"
metrics:
  duration_min: 18
  completed_date: "2026-06-14T21:59:06Z"
  tasks_completed: 2
  files_modified: 5
---

# Quick 260614-q6g: Redesign Clean & Elegante light-first — Summary

**One-liner:** Paleta light reconciliada (off-white #FAFBF9, verde da marca consistente, azul secundario em links/faixa/badges, sombras difusas) + hero da home com `<model-viewer>` auto-rotate alimentado pelo produto-3D em destaque e fallback elegante.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Reconciliar tokens light + azul secundario + sombras difusas + prova social | `0a9d35b` | `static/css/theme.css` |
| 2 | Expor produto-3D do hero (service + mapper + view) e hero model-viewer com fallback | `8faed13` | `mappers.py`, `services.py`, `views.py`, `home.html` |

## What Was Built

### Task 1 — Tokens light reconciliados

Tres blocos `[data-theme="light"]` em `theme.css` divergiam na cascata. O terceiro bloco (linhas ~1171-1177) sobrescrevia `--accent` com `#1eb457`/`#15914a` (verde diferente da marca), tornando o verde inconsistente.

Mudancas em `static/css/theme.css`:
- **Bloco 1** (~l678): `--bg` corrigido para `#FAFBF9` (off-white quente, nao branco puro), `--bg-soft` para `#F2F5F0`, bordas para `#E7EBE4`/`#F0F3EC`, sombras difusas `rgba(23,38,80,.20)`.
- **Bloco 2** (~l1161): sombras alinhadas ao mesmo valor do bloco 1.
- **Bloco 3** (~l1171): verde travado na paleta da marca (`#2FA84F`/`#43C266`/`#1E8C3E`) — nao mais `#1eb457`.
- **Tokens azuis novos**: `--accent-blue-soft: #E6F4FB` e `--accent-blue-ink: #0E5E84` adicionados ao `:root` e ao bloco light.
- **Links azuis**: `[data-theme="light"] .section-head .link` usa `var(--accent-blue)` (links "Ver tudo/catalogo").
- **Faixa de prova social**: `[data-theme="light"] .proof-strip` recebe `linear-gradient(110deg, var(--accent-soft), var(--accent-blue-soft))`.
- **Badge novo**: `[data-theme="light"] .badge-new` recebe fundo `--accent-blue-soft` e texto `--accent-blue-ink`.
- **Estilos do hero 3D**: `.gh-viewer`, `model-viewer`, `.gh-viewer-caption`, `.gh-viewer-stl` adicionados ao bloco `.geek-hero--clean` com sombras difusas e responsivo ≤760px.

### Task 2 — Hero 3D na home

- **`ProductMapper.to_dict`**: adicionou `has_3d`, `has_stl`, `model_3d_url`, `model_stl_url` (padrao `instance.model_3d.url if instance.model_3d else ""`). `to_detail` herda via `update`.
- **`CatalogService.get_hero_3d_product`**: retorna 1 produto-3D priorizando `is_featured`, ou `None` se nenhum ativo tiver `model_3d`. Reusa `ProductQuery.with_3d(limit=10)`.
- **`HomeView.get_context_data`**: adiciona `context["hero_3d"]` com import local ja existente.
- **`home.html`**: `.gh-deco` substituido por `.gh-viewer` com `<model-viewer auto-rotate camera-controls>` em ambos os ramos (`{% if hero_promo %}` e `{% else %}`). Fallback `.gh-deco` mantido quando `hero_3d` e falsy. Botao "Baixar STL" condicional a `has_stl`. Script CDN carregado via `{% block extra_js %}` gated por `{% if hero_3d %}`.

## Deviations from Plan

### Auto-added

**1. [Rule 2 - Completeness] hero_3d injetado em ambos os ramos do hero**
- **Found during:** Task 2 — template tinha dois branches (`{% if hero_promo %}` e `{% else %}`); o plano especificava substituir `.gh-deco` mas so mencionava um ramo.
- **Fix:** Viewer adicionado em ambos os ramos, garantindo que o 3D apareca com ou sem promocao ativa.
- **Commit:** `8faed13`

Nenhuma outra desvio — plano executado conforme especificado.

## Known Stubs

Nenhum. `model_3d_url` usa `instance.model_3d.url` (URL real do arquivo), nao valor hardcoded. O fallback `.gh-deco` e explicitamente intencional (documentado no plan).

## Self-Check: PASSED

- `static/css/theme.css` modificado e presente.
- `apps/catalog/mappers.py` contem `model_3d_url`.
- `apps/catalog/services.py` contem `get_hero_3d_product`.
- `apps/core/views.py` contem `hero_3d`.
- `apps/core/templates/core/home.html` contem `model-viewer`.
- Commits `0a9d35b` e `8faed13` existem em `git log`.
- `python manage.py check` sem erros (verificado apos cada task).
