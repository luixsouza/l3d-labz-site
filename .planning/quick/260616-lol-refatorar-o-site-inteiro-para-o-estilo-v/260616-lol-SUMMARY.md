---
phase: quick-260616-lol
plan: "01"
subsystem: frontend/css
tags: [rebrand, css, vibrante-maker, home, instagram]
dependency_graph:
  requires: []
  provides: [vibrante-maker-style, equal-height-cards, ig-cta-home]
  affects: [static/css/theme.css, apps/core/templates/core/home.html]
tech_stack:
  added: ["--ink token", "--offset-shadow token", ".ig-cta class", "color-mix() para thumbs pastel"]
  patterns: ["CSS appendix via cascata (sem reescrita)", "design tokens herdados", "color-mix() pastel derivado de --ph-accent"]
key_files:
  created: []
  modified:
    - static/css/theme.css
    - apps/core/templates/core/home.html
decisions:
  - "Apêndice CSS único no fim do arquivo vence a cascata — zero remoção de layers anteriores"
  - "--ink claro no dark (rgba branco-esverdeado) para bordas legíveis sobre fundo escuro"
  - "color-mix() deriva pastel de --ph-accent sem tocar no template do card (sem classes c0-c7)"
  - "hero split fix reafirmado dentro do apêndice (grid 1.15fr .85fr !important) para garantir prioridade"
  - "CTA WhatsApp removido da home; about.html intocado conforme escopo"
metrics:
  duration: "5 min"
  completed: "2026-06-16T18:48:06Z"
  tasks_completed: 2
  files_modified: 2
---

# Quick 260616-lol: Estilo Vibrante Maker (sketch 002-B) via apêndice CSS + CTA Instagram na home

**One-liner:** Apêndice "Vibrante Maker" ao fim de theme.css (tokens --ink/--offset-shadow, bordas duras, sombra-offset, thumbs pastel, hero degradê verde→azul com pontos) + CTA final da home trocado de WhatsApp fictício para bloco Instagram (@l3d_labz).

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Apêndice Vibrante Maker (tokens, botões, cards, hero) | f299d3f | static/css/theme.css |
| 2 | CTA Instagram na home + altura igual cards | 13c09fb | apps/core/templates/core/home.html |

## What Was Built

### Task 1 — Apêndice "Vibrante Maker" no theme.css

Bloco de ~290 linhas adicionado ao fim de `static/css/theme.css` após o FIX do split do hero (linha 2644). Vence todos os layers anteriores (v3/v4/Atelier/Clean & Elegante) por ordem de cascata.

**Tokens novos:**
- `--ink`: `rgba(233,237,246,.85)` no dark (branco-esverdeado para bordas visíveis sobre fundo escuro); `#0C1F15` no light (verde-tinta maker do mockup)
- `--offset-shadow`: `4px 4px 0 var(--ink)` — usado em todos os offsets para consistência
- `--offset-shadow-hover`: `6px 6px 0 var(--ink)` — versão de hover

**Componentes:**
- `.btn-primary`: borda 2.5px solid `--ink` + offset; hover translada (-1px,-1px) e aumenta offset; active translada (2px,2px) e reduz (efeito "pressionado")
- `.product-card`: borda 2.5px + hover translate(-2px,-2px) com offset 6px; substitui translateY + shadow difusa
- `.product-thumb`: bloco pastel via `color-mix(in srgb, --ph-accent 16%, #fff)`; dark usa mistura com `--bg-card`; borda inferior dura 2.5px
- `.badge-new` / `.badge-discount`: borda 2px + border-radius:8px; `.badge-soft` borda 1.5px
- `.pill` / `.cat-chip`: borda 2.5px; `.pill.active` fundo `--ink` + texto `#7CF29B`
- `.product-name`: `-webkit-line-clamp:2` + `min-height:2.4em` (normaliza altura entre cards)
- `.product-actions`: `margin-top:auto`; `.price-row`: `margin-top:0` (corrige duplo margin-top que impedia alinhamento do botão na base)
- `.geek-hero--clean`: degradê `linear-gradient(135deg, --accent 0%, #27a07a 45%, --accent-blue 100%)` + textura de pontos via `::before` (`radial-gradient rgba(255,255,255,.18) 2px, 26px 26px`) + borda 3px + border-radius:var(--radius-lg); overrides de light e dark; botões primários brancos com offset, ghost outline branco
- `.gh-viewer model-viewer`: cartão branco com borda 3px + offset 8px (estilo hero-card do mockup)
- `.ig-cta`: degradê Instagram `linear-gradient(120deg, #F58529, #DD2A7B 55%, #515BD4)` + borda 3px + offset 7px + layout flex responsivo (empilha em ≤600px)
- FIX split hero reafirmado: `grid-template-columns: 1.15fr .85fr !important` (≤820px: 1fr)

### Task 2 — CTA Instagram na home

Bloco `<section class="section">` (linhas 196-209 do original) substituído:
- Removido: `.shop-cta` com `wa.me` falso e ícone WhatsApp
- Adicionado: `.ig-cta` com ícone `#i-instagram`, h3 "Cola no nosso Instagram!", subtítulo pt-br com `@l3d_labz`, botão "Seguir @l3d_labz" → `{{ SITE.instagram }}` (target=_blank, rel=noopener)
- `about.html` intocado (fora do escopo)

## Smoke Tests (HTTP 200)

| URL | Status |
|-----|--------|
| `/` (home) | 200 — ig-cta renderizado, instagram.com/l3d_labz presente, sem wa.me no HTML da home |
| `/catalogo/` | 200 |
| `/catalogo/modelos-3d/` | 200 |
| `/carrinho/` | 200 |
| `/calculadora/` | 200 |
| `/conta/entrar/` | 200 |

Django `manage.py check`: 0 issues.

**Pendente (orquestrador):** Verificação visual no browser (light/dark, cards altura-igual, hover dos botões, model-viewer 3D, FAB Instagram).

## Deviations from Plan

None — plano executado exatamente como escrito. O FIX do split do hero foi reafirmado dentro do apêndice (como exigido pelo plano) sem necessidade de mudanças estruturais.

## Known Stubs

None. `{{ SITE.instagram }}` é resolvido pelo context processor existente em `config/settings/base.py` (valor: `https://instagram.com/l3d_labz`).

## Threat Flags

None. Nenhuma nova superfície de rede, endpoint, rota de auth ou mudança de schema introduzida. Mudanças limitadas a CSS estático e um template de apresentação.

## Self-Check: PASSED

- `static/css/theme.css` modificado: confirmed (git diff f299d3f)
- `apps/core/templates/core/home.html` modificado: confirmed (git diff 13c09fb)
- Commits f299d3f e 13c09fb existem: confirmed (`git log --oneline -5`)
- 19/19 verificações CSS passaram (Vibrante Maker, --ink, --offset-shadow, .btn-primary, .product-card, thumbs pastel, borda inferior, line-clamp, product-actions, badges, pills, hero gradient, hero pontos, hero border, light override, .ig-cta, ig-cta gradient, split fix, chaves balanceadas)
- Verificações do plano (Task 1 e Task 2) passaram todas


## Follow-up (mockup fidelity)
- Skin autoritativo (vence [data-theme]/!important) — hero/cards/header/faixas.
- Barra de categorias da home com pílula "Todas" ativa (igual mockup).
- **Sistema de botões maker em TODO o site** (btn/btn-ghost/icon-btn/Aplicar, não só primary) — auditado página a página. Commits c82986f, a359736.
