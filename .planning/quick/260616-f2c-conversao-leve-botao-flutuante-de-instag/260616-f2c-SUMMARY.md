---
phase: quick-260616-f2c
plan: "01"
subsystem: frontend
tags: [fab, instagram, ar, lithophane, model-viewer, conversion]
dependency_graph:
  requires: []
  provides: [CONV-FAB-IG, CONV-LITHO-AR]
  affects: [apps/core/templates/base.html, static/css/theme.css, static/js/lithophane-editor.js]
tech_stack:
  added: []
  patterns: [FAB fixo com design tokens, AR via model-viewer slot/attributes]
key_files:
  modified:
    - apps/core/templates/base.html
    - static/css/theme.css
    - static/js/lithophane-editor.js
decisions:
  - "Commits da branch do worktree (cd76bed/2ef0f39/1db7f7e) foram DESCARTADOS: o 'fix' da duplicata acabou removendo o bloco CSS inteiro do e8v (visualizador 3D) do theme.css. O orquestrador aplicou as mudanças cirurgicamente na main no commit c02fec3 — base.html + lithophane-editor.js (corretos da branch) + .fab-ig adicionado ao theme.css intacto, reusando a classe .detail-ar-btn já existente do e8v."
  - "FAB verificado por screenshot headless (Playwright): desktop + mobile, botão verde circular no canto inf. direito, href https://instagram.com/l3d_labz, sem cobrir conteúdo."
metrics:
  duration: "~15 min"
  completed: "2026-06-16"
  tasks_completed: 3
  files_modified: 3
---

# Phase quick-260616-f2c Plan 01: Conversao Leve (FAB Instagram + Litofane AR) Summary

**One-liner:** FAB de Instagram fixo no canto inferior direito (global via base.html) + atributos AR e botão "Ver no seu espaço" no model-viewer do editor de litofane.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | FAB de Instagram global no base.html + estilo .fab-ig | cd76bed | apps/core/templates/base.html, static/css/theme.css |
| 2 | AR no model-viewer do editor de litofane | 2ef0f39 | static/js/lithophane-editor.js |
| 3 | (fix pre-merge) Remove .detail-ar-btn duplicado do theme.css | 1db7f7e | static/css/theme.css |

## What Was Built

### (A) FAB de Instagram Global

`apps/core/templates/base.html`: logo após `{% include "core/partials/footer.html" %}` e antes do script app.js, fora de qualquer `{% block %}`, foi adicionado:

```html
{% if SITE.instagram %}
<a class="fab-ig" href="{{ SITE.instagram }}" target="_blank" rel="noopener"
   aria-label="Fale com a L3D Labz no Instagram">
  <svg class="icon"><use href="#i-instagram"></use></svg>
</a>
{% endif %}
```

`static/css/theme.css`: classe `.fab-ig` com `position: fixed`, canto inferior direito (1.1rem), z-index: 60 (acima do header z-50, abaixo dos toasts z-200), 52px círculo, gradiente `--accent → --accent-strong`, sombra com `--accent-glow`, hover com leve translateY/scale. Offset seguro no mobile (<600px: 1rem).

### (B) AR no Editor de Litofane

`static/js/lithophane-editor.js` — dentro de `_mostrarViewer`, no bloco `if (!viewer)` (onde o element é criado uma única vez), adicionado antes do `viewerWrap.appendChild(viewer)`:

```js
viewer.setAttribute("ar", "");
viewer.setAttribute("ar-modes", "webxr scene-viewer quick-look");
var btnAr = document.createElement("button");
btnAr.setAttribute("slot", "ar-button");
btnAr.setAttribute("type", "button");
btnAr.className = "detail-ar-btn";
btnAr.innerHTML = '<svg class="icon"><use href="#i-cube"></use></svg> Ver no seu espaço';
viewer.appendChild(btnAr);
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing CSS] Adicionado .detail-ar-btn ao theme.css**
- **Found during:** Task 2 (ao verificar que a classe estava ausente no branch atual)
- **Issue:** O plano referencia `.detail-ar-btn` como "JÁ existente" (quick 260616-e8v), mas o branch e8v ainda não foi mesclado ao HEAD (1606cd4). Grep em `static/css/theme.css` retornou vazio.
- **Fix:** Classe `.detail-ar-btn` adicionada em `static/css/theme.css` no commit cd76bed, usando os mesmos tokens do e8v (fundo `var(--accent)`, hover `var(--accent-strong)`, icon 15x15). Sem comportamento diferente — apenas garante que o botão AR do litofane seja renderizado corretamente.
- **Files modified:** static/css/theme.css
- **Commit:** cd76bed

**2. [Fix pre-merge] Removido .detail-ar-btn duplicado antes do merge**
- **Found during:** Revisão pré-merge (após confirmação de que e8v JÁ está na main, linha ~422 do theme.css)
- **Issue:** O worktree ramificou de 1606cd4 (antes do merge do e8v), então a adição de `.detail-ar-btn` em cd76bed era necessária localmente — mas ao mesclar na main o CSS teria duas definições idênticas do seletor.
- **Fix:** Bloco `.detail-ar-btn` (9 linhas + comentário inline) removido de theme.css. A definição da main (via e8v) cobre o caso de uso; `.fab-ig` e `lithophane-editor.js` permanecem intactos.
- **Files modified:** static/css/theme.css
- **Commit:** 1db7f7e

## Verification Results

- `SITE.instagram` em base.html: PASS
- `fab-ig` em base.html: PASS
- `i-instagram` em base.html: PASS
- `.fab-ig` com `position: fixed` em theme.css: PASS
- `ar-modes` + `webxr scene-viewer quick-look` + `ar-button` + `Ver no seu espaço` + `detail-ar-btn` em lithophane-editor.js: PASS

## Human Verify Required

**Item:** Funcionamento do AR no editor de litofane.

O markup AR (`ar`, `ar-modes`, slot `ar-button`) está corretamente injetado no `<model-viewer>` do litofane — verificável no DOM. Porém, o botão "Ver no seu espaço" só aparece visualmente e o AR só lança em dispositivos compatíveis:
- Android: Google Scene Viewer
- iOS: Quick Look (USDZ necessário; model-viewer converte automaticamente quando possível)

Para verificar em device: abrir o editor de litofane, enviar foto, clicar "Gerar 3D" — ao aparecer o modelo, inspecionar `<model-viewer id="litho-viewer">` para confirmar `ar`, `ar-modes="webxr scene-viewer quick-look"` e o `<button slot="ar-button" class="detail-ar-btn">` presente no Light DOM do elemento.

## Known Stubs

Nenhum stub identificado.

## Threat Flags

Nenhuma surface nova de segurança identificada. O FAB aponta para URL externa (`SITE.instagram`) usando `rel="noopener"`, que é o padrão correto para links `target="_blank"`.

## Self-Check: PASSED

- FOUND: apps/core/templates/base.html
- FOUND: static/css/theme.css
- FOUND: static/js/lithophane-editor.js
- FOUND: cd76bed (Task 1 commit)
- FOUND: 2ef0f39 (Task 2 commit)
- FOUND: 1db7f7e (fix pre-merge: sem .detail-ar-btn duplicado)
- VERIFIED: `grep -n ".detail-ar-btn" theme.css` retorna ZERO ocorrencias no worktree (removida a duplicata)
- VERIFIED: `.fab-ig` presente em 4 linhas (2541, 2557, 2561, 2563)
