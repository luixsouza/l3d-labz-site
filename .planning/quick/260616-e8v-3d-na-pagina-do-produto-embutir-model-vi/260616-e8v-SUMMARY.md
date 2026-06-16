---
phase: quick-260616-e8v
plan: "01"
subsystem: catalog/product-detail
tags: [3d-viewer, model-viewer, progressive-enhancement, ux]
dependency_graph:
  requires: [Phase 02 product model fields has_3d/has_stl/model_3d_url/model_stl_url, Phase 03 model-viewer CDN pattern]
  provides: [visualizador 3D na página de detalhe do produto, toggle Fotos/3D]
  affects: [apps/catalog/templates/catalog/product_detail.html, static/js/app.js, static/css/theme.css, apps/core/templates/core/partials/icons.html]
tech_stack:
  added: []
  patterns: [web component model-viewer @4.3.1 CDN ES module, progressive enhancement toggle via data attrs, CSS [data-media-panel] show/hide]
key_files:
  created: []
  modified:
    - apps/catalog/templates/catalog/product_detail.html
    - static/js/app.js
    - static/css/theme.css
    - apps/core/templates/core/partials/icons.html
decisions:
  - reveal="interaction" para lazy-load do GLB (não baixa até o cliente abrir a aba 3D)
  - CSS [data-media-panel]{display:none} + .active{display:block} garante no-JS safe (painel Fotos tem active no HTML)
  - Scoping do toggle por .detail-media-wrap (sem vazar para outros elementos da página)
  - #i-download adicionado ao sprite SVG (estava referenciado em home.html mas ausente)
metrics:
  duration: "~15 min"
  completed: "2026-06-16T13:22:13Z"
  tasks_completed: 2
  files_changed: 4
---

# Quick 260616-e8v: Visualizador 3D na Página do Produto — Summary

**One-liner:** Toggle Fotos/3D com model-viewer (GLB lazy via reveal="interaction", AR no celular, STL condicional) embutido na página de detalhe, sem tocar em view/service/mapper.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Toggle Fotos/3D + model-viewer no detalhe | 9839146 | product_detail.html, theme.css, icons.html |
| 2 | Lógica de toggle em app.js | 53ce2d4 | static/js/app.js |

## What Was Built

### Task 1 — Template + CSS

- `.detail-media-wrap` envolve toda a área de mídia; tabs de toggle (`data-media-tab="fotos"` / `data-media-tab="3d"`) só aparecem quando `product.has_3d`.
- Painel Fotos (`data-media-panel="fotos"`) tem classe `active` por padrão — contém o carrossel/foto existente intacto.
- Painel 3D (`data-media-panel="3d"`) contém o `<model-viewer>` com:
  - `src="{{ product.model_3d_url }}"` e `poster="{{ product.image_url }}"` (exibe foto até interagir)
  - `reveal="interaction"` — **GLB não é baixado até o cliente abrir a aba 3D**
  - `camera-controls`, `auto-rotate`, `ar`, `ar-modes="webxr scene-viewer quick-look"`
  - `slot="ar-button"` com copy "Ver no seu espaço" (model-viewer esconde automaticamente em dispositivos sem AR)
  - Legenda "arraste pra girar · pinça pra zoom"
  - Botão "Baixar STL" só dentro de `{% if product.has_stl %}`
- Script CDN `model-viewer@4.3.1` carregado em `{% block extra_js %}` gated por `{% if product.has_3d %}` — produtos sem 3D não carregam o script.
- CSS: `.detail-media-tabs`, `.detail-media-tab` (pill com tokens dark/light), `.detail-3d-panel`, `.detail-stl-btn`, `.detail-ar-btn`, `[data-media-panel]{display:none}` / `.active{display:block}`.

### Task 2 — JavaScript

- Bloco `/* --- toggle fotos/3d (detalhe) --- */` adicionado dentro do IIFE existente.
- Scoped por `.detail-media-wrap`: seleciona todos os `[data-media-tab]` dentro do wrapper, ao clicar ativa o botão e exibe o painel correspondente.
- `aria-selected` atualizado nos botões de tab para acessibilidade.
- **Progressive enhancement**: sem JS, o painel Fotos já tem `active` no HTML e fica visível; o toggle é melhoria, não requisito.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Ícone #i-download ausente do sprite SVG**
- **Found during:** Task 1 — ao tentar usar `#i-download` no botão STL conforme o plano
- **Issue:** O sprite `icons.html` não tinha o símbolo `#i-download`, mas ele já era referenciado em `home.html` (botão "Baixar STL" do hero) — ícone seria invisível nos dois lugares
- **Fix:** Adicionado `<symbol id="i-download">` com ícone de seta de download ao sprite SVG
- **Files modified:** `apps/core/templates/core/partials/icons.html`
- **Commit:** 9839146

## Human Verification Required

**IMPORTANTE:** O Chrome headless NÃO renderiza WebGL — verificação do viewer 3D é no navegador real.

### Passos de verificação no navegador:

1. `python manage.py runserver` e abrir um produto COM modelo 3D (ex.: `/catalogo/modelos-3d/`)
2. Confirmar que o toggle "Fotos / 3D" aparece acima da mídia, começando em Fotos (carrossel funcionando)
3. Clicar em "3D": o model-viewer deve carregar e permitir girar (arrastar), zoom (scroll/pinça) e pan
   - **Verificar no Network tab:** o arquivo `.glb` NÃO deve aparecer na carga inicial — só ao abrir a aba 3D
4. Confirmar botão "Baixar STL" (só para produtos com STL) e que o download funciona
5. No celular ou DevTools device mode: confirmar botão AR "Ver no seu espaço"
6. Abrir produto SEM modelo 3D: sem toggle, sem viewer — só fotos, layout idêntico ao atual
7. Confirmar aparência nos temas claro e escuro

## Known Stubs

Nenhum. Os campos `model_3d_url`, `model_stl_url`, `has_3d`, `has_stl` já estavam expostos pelo `ProductMapper.to_detail` (Phase 02).

## Threat Flags

Nenhuma nova superfície de rede ou auth path introduzida. O model-viewer usa `src` de URL de media já existente (field `model_3d` do produto) e o download STL usa `href` de media — mesma trust boundary do carrossel de fotos.

## Self-Check: PASSED

- FOUND: apps/catalog/templates/catalog/product_detail.html
- FOUND: static/js/app.js
- FOUND: static/css/theme.css
- FOUND: apps/core/templates/core/partials/icons.html
- FOUND: commit 9839146 (Task 1)
- FOUND: commit 53ce2d4 (Task 2)
- Template syntax valid: `get_template('catalog/product_detail.html')` — OK
- 12/12 pattern checks passed (model-viewer, has_3d/has_stl gates, data-media-tab/panel, reveal=interaction, ar-modes, extra_js, model_3d_url, model_stl_url, ar-button slot, active panel on load)
