---
task_id: 260616-gj3
phase: quick
plan: 260616-gj3
subsystem: catalog
tags: [catalog, 3d-models, filters, pagination, css, grid]
key-files:
  modified:
    - apps/catalog/queries.py
    - apps/catalog/services.py
    - apps/catalog/views.py
    - apps/catalog/templates/catalog/product_list.html
    - apps/catalog/templates/catalog/partials/product_card.html
    - static/css/theme.css
  deleted:
    - apps/catalog/templates/catalog/models_3d.html
decisions:
  - "only_3d como flag em browse/search vs. endpoint separado — flag mantém DRY (reutiliza product_list.html)"
  - "Filtro color '4' usa __gte=4 (4+ cores) em vez de valor exato"
  - "Filtro filament usa faixas string ('0-50', '50-150', '150+') — mais elegante que min/max"
  - "Sorts filament_asc/desc: anotação _unknown_fil para zeros ao fim sem violar ORM layer"
  - "PAGE_SIZE 12 -> 24 para grid mais denso"
  - "models_3d.html deletado — view não o referencia mais; apenas docs de planejamento referenciavam"
metrics:
  duration: "~65 minutos"
  completed: "2026-06-16T15:04:48Z"
  tasks_completed: 3
  files_modified: 6
  files_deleted: 1
---

# Quick Task 260616-gj3: Loja mais rica — /modelos-3d/ vira catálogo completo

Catálogo 3D completo com paginação, filtros por nº de cores e faixa de filamento, novas ordenações (filamento crescente/decrescente com zeros no fim, mais cores), paginação que preserva todos os filtros via `{% querystring %}` do Django 5.2, grid mais denso e chip de specs no card.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Camada de dados — only_3d, filtros color/filament, novos sorts, PAGE_SIZE=24 | 3119899 | queries.py, services.py |
| 2 | Views + templates — catálogo 3D parametrizado, paginação, chip no card | 3b78b37 | views.py, product_list.html, product_card.html, models_3d.html (del) |
| 3 | CSS — grid denso (210px), stagger capado, .spec-chip | 603d9f2 | theme.css |

## What Was Built

### Task 1 — Camada de dados

**`ProductQuery.search`** recebeu três novos kwargs:
- `only_3d=False` — `.exclude(model_3d="")` quando True
- `color=None` — filtra `color_count`; "4" usa `__gte=4` (4+ cores)
- `filament=None` — faixas "0-50" / "50-150" / "150+"; `filament_grams=0` nunca casa

Novos sorts sem quebrar os antigos:
- `filament_asc` / `filament_desc` — anota `_unknown_fil=Case(When(filament_grams=0, then=1), default=0)` e ordena `("_unknown_fil", "±filament_grams", "-sales_count")`, garantindo zeros sempre no fim
- `colors_desc` — `("-color_count", "-sales_count")` (color_count tem default=1, sem "desconhecido")

**`CatalogService.browse`**:
- `PAGE_SIZE` 12 → 24
- Novo param `only_3d=False`; lê `color` e `filament` de `params`; repassa ao `ProductQuery.search`
- Contexto retorna: `only_3d`, `active_color`, `active_filament`
- Método `gallery()` removido (nada o chamava fora da view que foi atualizada)

### Task 2 — Views + templates

**`views.models_3d`** virou:
```python
page = request.GET.get("page", 1)
context = CatalogService.browse(request.GET, page=page, only_3d=True)
return render(request, "catalog/product_list.html", context)
```

**`product_list.html`** parametrizado para servir `/catalogo/` e `/catalogo/modelos-3d/`:
- Hero 3D condicional (`{% if only_3d %}`) com eyebrow "Visualização 3D"
- URL-base dinâmica via `{% url ... as base_url %}` + `{% with %}` — forms e pills apontam para o escopo certo
- Dois novos `<select>` na filter bar: nº de cores e faixa de filamento (onchange submit)
- Três novas opções no `<select name="sort">`: Menos filamento / Mais filamento / Mais cores
- Paginação refatorada para `{% querystring page=num %}` — preserva automaticamente todos os GET params (q, categoria, material, min, max, color, filament, sort)
- Empty state com link para `base_url` correto (não hardcoded para `/catalogo/`)

**`product_card.html`** — chip condicional:
```html
{% if product.filament_grams %}<span class="spec-chip">
  <svg class="icon"><use href="#i-layers"></use></svg>
  {{ product.filament_display }} · {{ product.color_count }} cor{{ product.color_count|pluralize }}
</span>{% endif %}
```
Usando `|pluralize` para "cor/cores" em pt-br. Não quebra o card da home (aditivo e condicional).

**`models_3d.html`** — deletado (a view não o referencia mais).

### Task 3 — CSS

**Grid mais denso:**
- Linha 252: `minmax(232px, 1fr)` → `minmax(210px, 1fr)`
- Override linha ~1414: `minmax(238px, 1fr)` → `minmax(210px, 1fr)`, gap `1.5rem` → `1.3rem`
- Mobile: `@media (max-width: 520px)` → 2 colunas; `@media (max-width: 340px)` → 1 coluna

**Stagger capado (elimina "vazão" branca):**
- Antes: `transition-delay: calc(var(--i) * 70ms)` — com 24 cards, `--i` chegava a 23 = 1610ms de delay
- Depois: `transition-delay: min(calc(var(--i) * 35ms), 420ms)` — nenhum card atrasa mais que 420ms
- `prefers-reduced-motion`: intacto (zera `.reveal`)

**`.spec-chip`:**
```css
.spec-chip { display:inline-flex; align-items:center; gap:.35rem; font-size:.72rem;
  color:var(--text-dim); background:var(--bg-soft); border:1px solid var(--border-soft);
  border-radius:999px; padding:.22rem .6rem; }
.spec-chip .icon { width:.95em; height:.95em; color:var(--accent-2); }
```
Usa tokens (inverte corretamente no tema claro).

## Verification Results

Verificação executada via Django shell + test Client com DB local populado (30 produtos com model_3d, filament_grams variados: 0/30/80/120/200/350):

| Check | Result |
|-------|--------|
| `ProductQuery.search(sort='filament_asc')` — zeros ao fim | PASS |
| `ProductQuery.search(color='2')` — filtra color_count=2 | PASS |
| `ProductQuery.search(filament='50-150')` — filtra faixa correta | PASS |
| `GET /catalogo/modelos-3d/?color=2&filament=50-150&sort=filament_asc` → 200 | PASS |
| `name="color"` e `name="filament"` no HTML | PASS |
| `filament_asc` no HTML (sort options) | PASS |
| `GET /catalogo/?sort=colors_desc` → 200 | PASS |
| `spec-chip` renderizado para produtos com filament_grams > 0 | PASS |
| `spec-chip` ausente quando filament_grams = 0 (condicional `{% if %}`) | PASS |
| `{% querystring %}` no template (grep) | PASS |
| `manage.py check` — 0 issues | PASS |
| `PAGE_SIZE == 24` | PASS |
| `only_3d`, `active_color`, `active_filament` no contexto de browse | PASS |

## Deviations from Plan

### Auto-fixed Issues

Nenhum bug encontrado. O plano foi executado exatamente como especificado, com uma pequena diferença:

**Adaptação de ambiente:** A verificação usou `Client(SERVER_NAME='localhost')` em vez do padrão `Client()` porque o dev settings não tem `'testserver'` em `ALLOWED_HOSTS`. O comportamento real na aplicação é idêntico.

## Known Stubs

Nenhum. Todos os campos (`filament_grams`, `color_count`, `filament_display`) já existiam no model e eram expostos pelo mapper. Nenhum dado mockado ou placeholder introduzido.

## Threat Flags

Nenhum. Apenas leitura/filtragem em endpoints existentes. Nenhuma nova superfície de rede, auth, upload ou schema.

## Self-Check: PASSED

- `apps/catalog/queries.py` — modificado com only_3d/color/filament/novos sorts
- `apps/catalog/services.py` — PAGE_SIZE=24, browse com only_3d/color/filament
- `apps/catalog/views.py` — models_3d usa browse+product_list.html
- `apps/catalog/templates/catalog/product_list.html` — parametrizado, querystring pagination
- `apps/catalog/templates/catalog/partials/product_card.html` — spec-chip condicional
- `static/css/theme.css` — grid 210px, stagger capado, .spec-chip
- `apps/catalog/templates/catalog/models_3d.html` — DELETADO (verificado via git status)
- Commits 3119899, 3b78b37, 603d9f2 existem no git log
